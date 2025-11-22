import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import torch.nn as nn
from torch import optim

# 设置设备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# 数据预处理 - 添加标准化
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))  # MNIST的标准参数
])

# 加载数据集
train_data = datasets.MNIST(
    root='data',
    train=True,
    transform=transform,
    download=True,
)
test_data = datasets.MNIST(
    root='data',
    train=False,
    transform=transform
)

# 修改数据加载器设置
loaders = {
    'train': DataLoader(train_data, batch_size=100, shuffle=True, num_workers=0),
    'test': DataLoader(test_data, batch_size=100, shuffle=False, num_workers=0)
}

# CNN模型定义
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 16, 5, 1, 2),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(16, 32, 5, 1, 2),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.out = nn.Linear(32 * 7 * 7, 10)
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = x.view(x.size(0), -1)
        output = self.out(x)
        return output

# 初始化模型
cnn = CNN().to(device)
loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(cnn.parameters(), lr=0.01)  

# 训练函数
def train(num_epochs, cnn, loaders):
    cnn.train()
    total_step = len(loaders['train'])
    
    for epoch in range(num_epochs):
        for i, (images, labels) in enumerate(loaders['train']):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            output = cnn(images)
            loss = loss_func(output, labels)
            loss.backward()
            optimizer.step()
            
            if (i+1) % 100 == 0:
                print(f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{total_step}], Loss: {loss.item():.4f}')

# 测试函数 
def test():
    cnn.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in loaders['test']:
            images, labels = images.to(device), labels.to(device)
            outputs = cnn(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
        accuracy = 100 * correct / total
        print(f'Test Accuracy of the model on the 10000 test images: {accuracy:.2f}%')

if __name__ == "__main__":
    # 训练和测试
    num_epochs = 10
    train(num_epochs, cnn, loaders)
    test()
    
    # 保存模型
    torch.save(cnn.state_dict(), 'mnist_cnn_model.pth')


def load_model():
    model = CNN()
    model.load_state_dict(torch.load('mnist_cnn_model.pth'))
    model.eval()
    return model

def predict_digit(model, img_tensor):
    with torch.no_grad():
        output = model(img_tensor)
        pred = output.argmax(dim=1, keepdim=True)
    return pred.item()