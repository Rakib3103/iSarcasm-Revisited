# -*- coding: utf-8 -*-
"""iSarcasmRevisited.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AJfF-mSKd_GZxJIw6amN67a2MZEMwMhv
"""

!pip install transformers

import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import DataLoader, TensorDataset, RandomSampler
import torch
from sklearn.model_selection import train_test_split

"""Reading Train Data"""

train_data = pd.read_csv('/content/train.En.csv')
# print(train_data.columns)

texts = train_data['tweet'].tolist()
labels = train_data['sarcastic'].tolist()

"""Reading Test Data"""

test_data = pd.read_csv('/content/task_A_En_test.csv')
# print(test_data.columns)

test_texts = test_data['text'].tolist()
test_labels = test_data['sarcastic'].tolist()

"""Preprocessing using BERT tokenizer"""

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Remove NaN Values: Before tokenizing, ensure that your texts list doesn't have any nan values. We filter out these values.d
texts = [text for text in texts if pd.notna(text)]

# # Replace NaN Values: Alternatively, you can replace nan values with a placeholder string (like "[UNK]" which stands for "unknown" in BERT's vocabulary)
# texts = [text if pd.notna(text) else "[UNK]" for text in texts]


input_ids = [tokenizer.encode(text, add_special_tokens=True) for text in texts]

"""Padding input_ids"""

max_len = max([len(ids) for ids in input_ids])
input_ids = [ids + [0] * (max_len - len(ids)) for ids in input_ids]
input_ids = torch.tensor(input_ids)

"""Attention masks"""

attention_masks = [[float(id != 0) for id in ids] for ids in input_ids]

"""Equalize the lengths of input_ids and labels (OpenAI)"""

min_length = min(len(input_ids), len(labels))
input_ids = input_ids[:min_length]
labels = labels[:min_length]

"""Split Data (OpenAi)"""

from sklearn.model_selection import train_test_split

train_inputs, val_inputs, train_labels, val_labels, train_masks, val_masks = train_test_split(
    input_ids, labels, attention_masks, test_size=0.2, random_state=42)

"""Attention Mask (OpenAi)"""

attention_masks = [[1 if token_id > 0 else 0 for token_id in input_id] for input_id in input_ids]

"""Splitting into training and validation sets"""

train_inputs, val_inputs, train_labels, val_labels = train_test_split(input_ids, labels, test_size=0.2)
train_masks, val_masks = train_test_split(attention_masks, test_size=0.2)

"""Convert to PyTorch data types"""

train_inputs, val_inputs = torch.tensor(train_inputs), torch.tensor(val_inputs)
train_labels, val_labels = torch.tensor(train_labels), torch.tensor(val_labels)
train_masks, val_masks = torch.tensor(train_masks), torch.tensor(val_masks)

"""Create DataLoader"""

train_data = TensorDataset(train_inputs, train_masks, train_labels)
train_loader = DataLoader(train_data, sampler=RandomSampler(train_data), batch_size=32)

val_data = TensorDataset(val_inputs, val_masks, val_labels)
val_loader = DataLoader(val_data, batch_size=32)

"""Model"""

model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

"""Training"""

model.train()
for epoch in range(3):  # Number of epochs
    for batch in train_loader:
        inputs, masks, labels = batch
        optimizer.zero_grad()
        outputs = model(inputs, attention_mask=masks, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()

"""Preprocessing test data"""

test_input_ids = [tokenizer.encode(text, add_special_tokens=True) for text in test_texts]
test_input_ids = [ids + [0] * (max_len - len(ids)) for ids in test_input_ids]
test_input_ids = torch.tensor(test_input_ids)

"""Attention masks for test data"""

test_attention_masks = [[float(id != 0) for id in ids] for ids in test_input_ids]

"""Convert to PyTorch data types"""

test_inputs = torch.tensor(test_input_ids)
test_labels = torch.tensor(test_labels)
test_masks = torch.tensor(test_attention_masks)

"""Create DataLoader for test data"""

test_data = TensorDataset(test_inputs, test_masks, test_labels)
test_loader = DataLoader(test_data, batch_size=32)

"""Evaluation on test data"""

model.eval()
correct = 0
with torch.no_grad():
    for batch in test_loader:
        inputs, masks, labels = batch
        outputs = model(inputs, attention_mask=masks)
        predictions = torch.argmax(outputs.logits, dim=1)
        correct += (predictions == labels).sum().item()

print(f'Test Accuracy: {correct / len(test_labels)}')