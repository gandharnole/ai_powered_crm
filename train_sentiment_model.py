import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, SpatialDropout1D, LSTM, Dropout, Dense, Bidirectional
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("D:/Major project/sentiment_dataset.csv")
review_df = df[['Comment','Sentiment']]

# Drop neutral sentiment
review_df = review_df[review_df['Sentiment'] != 'Neutral']

# Map categorical sentiments to numeric values
label_map = {'Positive': 1, 'Negative': 0}
review_df['Sentiment'] = review_df['Sentiment'].map(label_map)

# Prepare text and labels
texts = review_df['Comment'].values
labels = review_df['Sentiment'].values

# Tokenization and padding
tokenizer = Tokenizer(num_words=5000)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
padded_sequences = pad_sequences(sequences, maxlen=200)

# Split data into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(padded_sequences, labels, test_size=0.2, random_state=42)

# Define the LSTM model with added regularization
model = Sequential([
    Embedding(input_dim=5000, output_dim=32, input_length=200),  # Correctly define input_dim and input_length
    SpatialDropout1D(0.2),  # Add SpatialDropout1D for better regularization
    Bidirectional(LSTM(64, dropout=0.5, recurrent_dropout=0.5)),  # Bidirectional LSTM
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])

# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Print model summary
model.summary()

# Train the model with validation
history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=5, batch_size=64)

# Plot accuracy
plt.plot(history.history['accuracy'], label='accuracy')
plt.plot(history.history['val_accuracy'], label='val_accuracy')
plt.legend()
plt.savefig('Accuracy_Plot.jpg')
plt.show()

# Plot loss
plt.plot(history.history['loss'], label='loss')
plt.plot(history.history['val_loss'], label='val_loss')
plt.legend()
plt.savefig('Loss_Plot.jpg')
plt.show()

# Save the model
model.save("sentiment_model.keras")
print("Model saved to 'sentiment_model.keras'")