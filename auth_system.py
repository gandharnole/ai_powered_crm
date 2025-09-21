import hashlib
import secrets
import sqlite3
import json
from datetime import datetime, timedelta
import streamlit as st

class AuthenticationSystem:
    def __init__(self, db_path="logs/crm.db"):
        self.conn = sqlite3.connect(db_path)
        self._setup_tables()
        
    def _setup_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
        ''')
        
        # Roles and permissions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL,
            permissions TEXT NOT NULL,
            description TEXT
        )
        ''')
        
        # Sessions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create default roles if they don't exist
        self._create_default_roles()
            
        self.conn.commit()
        
    def _create_default_roles(self):
        """Create default roles if they don't exist"""
        cursor = self.conn.cursor()
        
        # Check if default roles exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Admin role
            admin_permissions = json.dumps({
                "dashboard": ["view", "edit"],
                "customers": ["view", "edit", "delete"],
                "sales": ["view", "edit", "delete"],
                "service": ["view", "edit", "delete"],
                "esg": ["view", "edit", "delete"],
                "system": ["view", "edit", "export"],
                "users": ["view", "edit", "delete"],
                "analytics": ["view", "run"]
            })
            
            # Sales role
            sales_permissions = json.dumps({
                "dashboard": ["view"],
                "customers": ["view", "edit"],
                "sales": ["view", "edit"],
                "service": ["view"],
                "esg": ["view"],
                "analytics": ["view"]
            })
            
            # Service role
            service_permissions = json.dumps({
                "dashboard": ["view"],
                "customers": ["view"],
                "sales": ["view"],
                "service": ["view", "edit"],
                "analytics": ["view"]
            })
            
            # Read-only role
            readonly_permissions = json.dumps({
                "dashboard": ["view"],
                "customers": ["view"],
                "sales": ["view"],
                "service": ["view"],
                "esg": ["view"],
                "system": ["view"],
                "analytics": ["view"]
            })
            
            # Insert roles
            cursor.execute(
                "INSERT INTO roles (role_name, permissions, description) VALUES (?, ?, ?)",
                ("admin", admin_permissions, "Full system access")
            )
            
            cursor.execute(
                "INSERT INTO roles (role_name, permissions, description) VALUES (?, ?, ?)",
                ("sales", sales_permissions, "Sales team access")
            )
            
            cursor.execute(
                "INSERT INTO roles (role_name, permissions, description) VALUES (?, ?, ?)",
                ("service", service_permissions, "Service team access")
            )
            
            cursor.execute(
                "INSERT INTO roles (role_name, permissions, description) VALUES (?, ?, ?)",
                ("readonly", readonly_permissions, "Read-only access")
            )
            
            self.conn.commit()
    
    def _hash_password(self, password, salt):
        """Hash password with salt using SHA-256"""
        password_salt = password + salt
        hash_obj = hashlib.sha256(password_salt.encode())
        return hash_obj.hexdigest()
            
    def create_user(self, username, password, full_name, email, role="readonly"):
        """Create a new user with the specified role"""
        cursor = self.conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return {"status": "error", "message": "Username already exists"}
        
        # Check if role exists
        cursor.execute("SELECT id FROM roles WHERE role_name = ?", (role,))
        if not cursor.fetchone():
            return {"status": "error", "message": "Invalid role"}
        
        # Generate salt and hash password
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        
        # Insert new user
        cursor.execute(
            '''INSERT INTO users 
               (username, password_hash, salt, full_name, email, role, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (username, password_hash, salt, full_name, email, role, datetime.now().isoformat())
        )
        
        self.conn.commit()
        return {"status": "success", "message": "User created successfully"}
    
    def authenticate(self, username, password):
        """Authenticate a user with username and password"""
        cursor = self.conn.cursor()
        
        # Get user
        cursor.execute(
            "SELECT id, password_hash, salt, role, is_active FROM users WHERE username = ?", 
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return {"status": "error", "message": "Invalid username or password"}
        
        user_id, stored_hash, salt, role, is_active = user
        
        if not is_active:
            return {"status": "error", "message": "Account is inactive"}
        
        # Check password
        calculated_hash = self._hash_password(password, salt)
        if calculated_hash != stored_hash:
            return {"status": "error", "message": "Invalid username or password"}
        
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id)
        )
        
        # Create session
        session_id = self._create_session(user_id)
        
        # Get permissions for role
        permissions = self.get_permissions(role)
        
        self.conn.commit()
        return {
            "status": "success", 
            "message": "Authentication successful",
            "user_id": user_id,
            "role": role,
            "permissions": permissions,
            "session_id": session_id
        }
    
    def _create_session(self, user_id, expires_in_days=1):
        """Create a new session for the user"""
        session_id = secrets.token_hex(32)
        expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO sessions 
               (session_id, user_id, created_at, expires_at) 
               VALUES (?, ?, ?, ?)''',
            (session_id, user_id, datetime.now().isoformat(), expires_at)
        )
        
        return session_id
    
    def validate_session(self, session_id):
        """Validate a session and return user info if valid"""
        if not session_id:
            return None
            
        cursor = self.conn.cursor()
        
        # Get session
        cursor.execute(
            '''SELECT s.user_id, s.expires_at, u.username, u.role 
               FROM sessions s
               JOIN users u ON s.user_id = u.id
               WHERE s.session_id = ?''',
            (session_id,)
        )
        
        session = cursor.fetchone()
        if not session:
            return None
            
        user_id, expires_at, username, role = session
        
        # Check if expired
        if datetime.fromisoformat(expires_at) < datetime.now():
            return None
            
        # Get permissions
        permissions = self.get_permissions(role)
        
        return {
            "user_id": user_id,
            "username": username,
            "role": role,
            "permissions": permissions
        }
    
    def logout(self, session_id):
        """Log out a user by removing their session"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self.conn.commit()
        return {"status": "success", "message": "Logged out successfully"}
    
    def get_permissions(self, role):
        """Get permissions for a role"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT permissions FROM roles WHERE role_name = ?", (role,))
        result = cursor.fetchone()
        
        if not result:
            return {}
            
        return json.loads(result[0])
    
    def check_permission(self, role, module, action):
        """Check if a role has permission to perform an action on a module"""
        permissions = self.get_permissions(role)
        
        if not permissions:
            return False
            
        if module not in permissions:
            return False
            
        return action in permissions[module]
    
    def update_user(self, user_id, full_name=None, email=None, role=None, is_active=None):
        """Update user information"""
        cursor = self.conn.cursor()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if full_name is not None:
            update_fields.append("full_name = ?")
            params.append(full_name)
            
        if email is not None:
            update_fields.append("email = ?")
            params.append(email)
            
        if role is not None:
            # Verify role exists
            cursor.execute("SELECT id FROM roles WHERE role_name = ?", (role,))
            if not cursor.fetchone():
                return {"status": "error", "message": "Invalid role"}
                
            update_fields.append("role = ?")
            params.append(role)
            
        if is_active is not None:
            update_fields.append("is_active = ?")
            params.append(1 if is_active else 0)
            
        if not update_fields:
            return {"status": "error", "message": "No fields to update"}
            
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        params.append(user_id)
        
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            return {"status": "error", "message": "User not found"}
            
        self.conn.commit()
        return {"status": "success", "message": "User updated successfully"}
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password"""
        cursor = self.conn.cursor()
        
        # Get current password hash and salt
        cursor.execute(
            "SELECT password_hash, salt FROM users WHERE id = ?", 
            (user_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            return {"status": "error", "message": "User not found"}
            
        stored_hash, salt = result
        
        # Verify current password
        calculated_hash = self._hash_password(current_password, salt)
        if calculated_hash != stored_hash:
            return {"status": "error", "message": "Current password is incorrect"}
            
        # Generate new salt and hash
        new_salt = secrets.token_hex(16)
        new_hash = self._hash_password(new_password, new_salt)
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (new_hash, new_salt, user_id)
        )
        
        self.conn.commit()
        return {"status": "success", "message": "Password changed successfully"}
    
    def reset_password(self, username, new_password):
        """Admin function to reset a user's password"""
        cursor = self.conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            return {"status": "error", "message": "User not found"}
            
        user_id = result[0]
        
        # Generate new salt and hash
        new_salt = secrets.token_hex(16)
        new_hash = self._hash_password(new_password, new_salt)
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (new_hash, new_salt, user_id)
        )
        
        # Delete all sessions for this user
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        self.conn.commit()
        return {"status": "success", "message": "Password reset successfully"}
    
    def list_users(self):
        """Get a list of all users"""
        cursor = self.conn.cursor()
        
        cursor.execute(
            """SELECT id, username, full_name, email, role, created_at, 
                    last_login, is_active FROM users"""
        )
        
        columns = [column[0] for column in cursor.description]
        users = []
        
        for row in cursor.fetchall():
            user = dict(zip(columns, row))
            user['is_active'] = bool(user['is_active'])
            users.append(user)
            
        return users
    
    def create_role(self, role_name, permissions, description=""):
        """Create a new role with specified permissions"""
        cursor = self.conn.cursor()
        
        # Check if role already exists
        cursor.execute("SELECT id FROM roles WHERE role_name = ?", (role_name,))
        if cursor.fetchone():
            return {"status": "error", "message": "Role already exists"}
            
        # Insert role
        cursor.execute(
            "INSERT INTO roles (role_name, permissions, description) VALUES (?, ?, ?)",
            (role_name, json.dumps(permissions), description)
        )
        
        self.conn.commit()
        return {"status": "success", "message": "Role created successfully"}
    
    def update_role(self, role_name, permissions=None, description=None):
        """Update an existing role"""
        cursor = self.conn.cursor()
        
        # Check if role exists
        cursor.execute("SELECT id FROM roles WHERE role_name = ?", (role_name,))
        if not cursor.fetchone():
            return {"status": "error", "message": "Role not found"}
            
        # Build update query
        update_fields = []
        params = []
        
        if permissions is not None:
            update_fields.append("permissions = ?")
            params.append(json.dumps(permissions))
            
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
            
        if not update_fields:
            return {"status": "error", "message": "No fields to update"}
            
        query = f"UPDATE roles SET {', '.join(update_fields)} WHERE role_name = ?"
        params.append(role_name)
        
        cursor.execute(query, params)
        self.conn.commit()
        
        return {"status": "success", "message": "Role updated successfully"}
    
    def list_roles(self):
        """Get a list of all roles with their permissions"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT role_name, permissions, description FROM roles")
        
        roles = []
        for role_name, permissions_json, description in cursor.fetchall():
            roles.append({
                "role_name": role_name,
                "permissions": json.loads(permissions_json),
                "description": description
            })
            
        return roles
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()