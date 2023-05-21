# https://github.com/ajinkya98/PyTorchCNN/blob/master/train.py

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from Model_old import CNN
from BirdsongDataset import BirdsongDataset
from tqdm import tqdm


device = ("cuda" if torch.cuda.is_available() else "cpu")

transform = transforms.Compose(
        [
            transforms.Grayscale(),
            transforms.Resize((356, 356)),
            # transforms.RandomCrop((299, 299)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5), (0.5, 0.5)),
        ]
    )

num_epochs = 10
learning_rate = 0.00001
train_CNN = False
batch_size = 32
shuffle = True
pin_memory = True
num_workers = 1
data_source = "spectrograms"
train_data_annotations = "train_data.csv"
test_data_annotations = "train_data.csv"

train_set = BirdsongDataset(data_source,train_data_annotations,transform=transform)
test_set = BirdsongDataset(data_source,test_data_annotations,transform=transform)
train_loader = DataLoader(dataset=train_set, shuffle=shuffle, batch_size=batch_size,num_workers=num_workers,pin_memory=pin_memory)
validation_loader = DataLoader(dataset=test_set, shuffle=shuffle, batch_size=batch_size,num_workers=num_workers, pin_memory=pin_memory)

model = CNN(num_classes=len(train_set)).to(device)

criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

for name, param in model.inception.named_parameters():
    if "fc.weight" in name or "fc.bias" in name:
        param.requires_grad = True
    else:
        param.requires_grad = train_CNN

def check_accuracy(loader, model):
    if loader == train_loader:
        print("Checking accuracy on training data")
    else:
        print("Checking accuracy on validation data")

    num_correct = 0
    num_samples = 0
    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device=device)
            y = y.to(device=device)

            scores = model(x)
            predictions = torch.tensor([1.0 if i >= 0.5 else 0.0 for i in scores]).to(device)
            num_correct += (predictions == y).sum()
            num_samples += predictions.size(0)
        print(
            f"Got {num_correct} / {num_samples} with accuracy {float(num_correct)/float(num_samples)*100:.2f}"
        )
    model.train()
    return f"{float(num_correct)/float(num_samples)*100:.2f}"

def train():
    model.train()
    for epoch in range(num_epochs):
        loop = tqdm(train_loader, total = len(train_loader), leave = True)
        if epoch % 2 == 1:
            loop.set_postfix(val_acc = check_accuracy(validation_loader, model))
        for imgs, labels in loop:
            imgs = imgs.to(device)
            labels = labels.to(device)
            outputs = model(imgs)
            labels = labels#.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            loop.set_description(f"Epoch [{epoch}/{num_epochs}]")
            loop.set_postfix(loss = loss.item())

if __name__ == "__main__":
    train()