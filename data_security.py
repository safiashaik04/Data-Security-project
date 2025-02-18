# -*- coding: utf-8 -*-
"""Data Security.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Ydp1Mj8nFArKEQG7StKMz_czBlVuRZ9l

# ResNet + Deep CNN 2
"""

import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.nn.functional as F

# Function to load data
def dataloader(train_dataset, test_dataset):
    batch_size = 50  # Batch size for training
    # DataLoader for training (centralized, using all data)
    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=batch_size,
        shuffle=True
    )

    # DataLoader for testing (using entire test set)
    test_loader = DataLoader(
        dataset=test_dataset,
        batch_size=len(test_dataset),
        shuffle=False  # No need to shuffle test data
    )
    print(f'Training set has: {len(train_loader)} batches of data!')
    print(f'Test set has: {len(test_loader)} batch of data!')
    return train_loader, test_loader


# Load MNIST dataset
def load_data():
    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])

    train_dataset = torchvision.datasets.MNIST(root="./data/mnist", train=True, download=True, transform=transform)
    test_dataset = torchvision.datasets.MNIST(root="./data/mnist", train=False, download=True, transform=transform)

    print("The number of training data:", len(train_dataset))
    print("The number of testing data:", len(test_dataset))

    return dataloader(train_dataset, test_dataset)


# Define a simple ResNet-like backbone
class SimpleResNet(nn.Module):
    def __init__(self):
        super(SimpleResNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.layer1 = self._make_layer(16, 32, stride=2)
        self.layer2 = self._make_layer(32, 64, stride=2)

    def _make_layer(self, in_channels, out_channels, stride):
        layers = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
        ]
        return nn.Sequential(*layers)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.layer1(x)
        x = self.layer2(x)
        return x


# Define the hybrid model
class HybridModel(nn.Module):
    def __init__(self):
        super(HybridModel, self).__init__()
        self.feature_extractor = SimpleResNet()

        # Calculate feature dimension dynamically
        dummy_input = torch.randn(1, 1, 28, 28)
        feature_output = self.feature_extractor(dummy_input)
        self.feature_dim = feature_output.shape[1] * feature_output.shape[2] * feature_output.shape[3]

        self.classifier = nn.Sequential(
            nn.Linear(self.feature_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 10)  # MNIST has 10 classes
        )

    def forward(self, x):
        x = self.feature_extractor(x)
        x = x.view(x.size(0), -1)  # Flatten feature map
        x = self.classifier(x)
        return x


def main():
    # Check if GPU is available, else use CPU
    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    # Hyperparameters
    learning_rate = 0.0005
    epochs = 10

    # Load data
    train_loader, test_loader = load_data()

    # Instantiate the model
    model = HybridModel().to(device)

    # Loss function and optimizer
    lossFun = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Variable to store the best accuracy and model path
    best_accuracy = 0.0
    best_model_path = 'best_hybrid_model.pth'

    # Training loop
    for epoch in range(epochs):
        running_loss = 0.0
        running_acc = 0.0

        model.train()  # Start training mode

        for i, data in enumerate(train_loader):
            features, labels = data
            features, labels = features.to(device), labels.to(device)

            optimizer.zero_grad()  # Zero the gradients before the backward pass
            preds = model(features)
            loss = lossFun(preds, labels)

            loss.backward()  # Backpropagation
            optimizer.step()

            running_loss += loss.item()
            correct = (preds.argmax(dim=1) == labels).sum().item()
            accuracy = correct / labels.size(0)
            running_acc += accuracy

            if i % 100 == 99:  # Print every 100 batches
                print(f'epoch:{epoch+1}, index:{i+1}, loss:{running_loss/100:.6f}, acc:{running_acc/100:.2%}')
                running_loss = 0.0
                running_acc = 0.0

    # Evaluate on the test set
    with torch.no_grad():
        model.eval()
        num_correct = 0
        num_samples = 0
        for test_features, test_labels in test_loader:
            test_features, test_labels = test_features.to(device), test_labels.to(device)
            test_preds = model(test_features)

            _, test_preds = torch.max(test_preds, 1)
            num_correct += (test_preds == test_labels).sum().item()
            num_samples += len(test_labels)

        test_accuracy = num_correct / num_samples
        print(f'Test Accuracy: {test_accuracy:.2%}')

        if test_accuracy > best_accuracy:
            best_accuracy = test_accuracy
            torch.save(model.state_dict(), best_model_path)
            print(f"Best model saved with accuracy: {best_accuracy:.2%}")


if __name__ == '__main__':
    main()

