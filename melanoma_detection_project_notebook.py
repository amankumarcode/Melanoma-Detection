# -*- coding: utf-8 -*-
"""Melanoma-Detection-Project-Notebook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ja27uMGmK5Um1rK53rZeF00ajy9V3BEa

# MELANOMA DETECTION PROJECT NOTEBOOK
### Team: ML Squad 7

### Colab Code Link:
https://colab.research.google.com/drive/1ja27uMGmK5Um1rK53rZeF00ajy9V3BEa?usp=sharing
"""

import pandas as pd
import numpy as np
import torch
import torchvision
from torchsummary import summary
import torch.nn.functional as F
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, Subset, WeightedRandomSampler
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import StratifiedKFold, GroupKFold, KFold, train_test_split
from torch import optim
from torchvision import datasets, transforms, models
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
import os
import cv2
import time
import datetime
import warnings
import random
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
!pip install efficientnet_pytorch
import zipfile
from efficientnet_pytorch import EfficientNet
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report

#from google.colab import drive
#drive.mount('/content/drive')

with zipfile.ZipFile("/content/drive/MyDrive/melanoma_256.zip", 'r') as zip_ref:
    zip_ref.extractall("/content")

with zipfile.ZipFile("/content/drive/MyDrive/melanoma_external_256.zip", 'r') as zip_ref:
    zip_ref.extractall("/content")

with zipfile.ZipFile("/content/drive/MyDrive/x_train_32.npy.zip", 'r') as zip_ref:
    zip_ref.extractall("/content")

"""## Exploratory Data Analysis"""

train_df = pd.read_csv("/content/archive-2/train.csv")
train_df.head()

train_df.shape

"""### Count Plot of the Target Variables.
We can visualize the imbalance in the dataset.
"""

#sns.set(style="darkgrid")
ax = sns.countplot(x="target", data=train_df)
plt.xlabel("Target")
train_df["target"].value_counts()/len(train_df)*100

"""### Anatomy vs Target Variable
Head/neck and oral/genital areas are common sites for sampling the data.
"""

#sns.set(style="darkgrid")
ax = sns.barplot(x="target", y="anatom_site_general_challenge", data=train_df)
plt.xlabel("Target")
plt.ylabel("Anatomy Site")

#number of unique patients
len(train_df["patient_id"].unique())

"""### Benign vs Malignant Count Plot
Males have a high malignant count than females in this dataset.
"""

sex_df = train_df.groupby(['target','sex'])['benign_malignant'].count().to_frame().reset_index()
sns.catplot(x='target',y='benign_malignant', hue='sex',data=sex_df,kind='bar')
plt.ylabel('Count')
plt.xlabel('Benign vs Malignant')

with_disease = train_df[train_df["target"]==1]
with_disease.head()

with_disease.shape

print(with_disease.shape)
len(with_disease["patient_id"].unique())

"""### Age Distribution of People with Melanoma"""

sns.histplot(with_disease.drop_duplicates(subset=['patient_id'])["age_approx"],color="gold")
plt.xlabel("Age")

#People without disease
without_disease = [x for x in train_df["patient_id"].unique()  if x not in with_disease["patient_id"].unique()]
print(len(without_disease))

#Display images of Target label
def display_images(df):
  img_path = "/content/archive-2/train"
  fig=plt.figure(figsize=(6,6))
  columns = 2
  rows = 2
  for i in range(1, columns*rows +1):
      img = cv2.imread(img_path + '/' + df.iloc[i-1][0] + ".jpg")
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      fig.add_subplot(rows, columns, i)
      plt.title(df.iloc[i-1][6])
      plt.imshow(img)
  plt.show()

"""Malignant"""

display_images(train_df[train_df["target"] == 1])

"""Benign"""

display_images(train_df[train_df["target"] == 0])

"""# SVM and Logistic Regression
Taking an image size of 32*32 stored in npy file for the classification with SVM and Logistic Regression.
"""

x_train_32 = np.load('/content/x_train_32.npy')
x_train_32.shape

x_train_32 = x_train_32.reshape((x_train_32.shape[0], 32*32*3))
x_train_32.shape

y = train_df.target.values
y.shape

#Train Test Split
X_train, X_test, y_train, y_test = train_test_split(x_train_32,y,stratify = y,test_size=.1,random_state=42)

"""### PCA
Principal component analysis capturing 99% variance in the data.
"""

pca = PCA(n_components=0.99,whiten=True)
X_train = pca.fit_transform(X_train)
X_test = pca.transform(X_test)
print(X_train.shape)
print(X_test.shape)

#Performing 5-Fold Cross Validation for Logistic Regression
n_splits = 5
kf = KFold(n_splits=n_splits, shuffle=True, random_state=0)
train_split = np.zeros((X_train.shape[0],))
test_preds = 0
train_split.shape

avg_auc = []
for fold, (train_index, val_index) in enumerate(kf.split(X_train)):
    print("For Fold", fold+1)
    train_features = X_train[train_index]
    train_target = y_train[train_index]
    val_features = X_train[val_index]
    val_target = y_train[val_index]
    model = LogisticRegression(C=1, solver='lbfgs', multi_class='multinomial', max_iter=64)
    model.fit(train_features, train_target)
    val_pred = model.predict_proba(val_features)[:,1]
    train_split[val_index] = val_pred
    print("Fold AUC:", roc_auc_score(val_target, val_pred))
    avg_auc.append(roc_auc_score(val_target, val_pred))
    print("-"*40)
    test_preds += model.predict_proba(X_test)[:,1]/n_splits
    del train_features, train_target, val_features, val_target
print("Average K-fold AUC:", np.mean(avg_auc))

roc_auc_score(y_test, test_preds)

logistic_pred = model.predict(X_test)
print(classification_report(y_test,logistic_pred))

"""### SVM using radial basis function kernel"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# svm = SVC(kernel='rbf', probability=True, random_state=42)
# svm.fit(X_train, y_train)
# test_pred = model.predict_proba(X_test)[:,1]

roc_auc_score(y_test, test_pred)

svm_pred = model.predict(X_test)
print(classification_report(y_test,svm_pred))

"""# Deep Learning Based Methods
We have used a Custom CNN Network and a pretrained EfficientNet-B2 model. There are two methods that we used to tackle imbalance; undersampling and oversampling.
"""

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print (device)

class MelanomaDataset(Dataset):
    def __init__(self, df: pd.DataFrame, img_dir: str, train: bool = True, transforms = None):
        self.df = df
        self.img_dir = img_dir 
        self.transforms = transforms
        self.train = train
        
    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        img_path = os.path.join(self.img_dir, self.df.iloc[index]['image_name'] + '.jpg')
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        if self.transforms:
            img = self.transforms(img)
        if self.train:
            y = self.df.iloc[index]['target']
            return torch.tensor(img, dtype=torch.float32),torch.tensor(y, dtype=torch.float32)
        else:
            return torch.tensor(img, dtype=torch.float32)

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(3, 32, 5, padding=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 32, 5, padding=2)
        self.pool = nn.MaxPool2d(2, 2)                        
        self.conv3 = nn.Conv2d(32, 64, 5,padding=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv4 = nn.Conv2d(64, 128, 3,padding=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv5 = nn.Conv2d(128, 256, 3,padding=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(in_features = 8*8*324, out_features= 64)
        self.fc2 = nn.Linear(64, 1)
        self.BatchNorm1 = nn.BatchNorm2d(32)
        self.BatchNorm2 = nn.BatchNorm2d(32)
        self.BatchNorm3 = nn.BatchNorm2d(64)
        self.BatchNorm5 = nn.BatchNorm2d(128)
        self.BatchNorm6 = nn.BatchNorm2d(256)
        self.BatchNorm4 = nn.BatchNorm1d(64)
        self.dropout = nn.Dropout2d(p=0.5)  #0.1


    def forward(self, x):

        x = self.conv1(x)
        x = self.BatchNorm1(x)
        x = self.pool(F.relu(x))
        x = self.conv2(x)
        x = self.BatchNorm2(x)
        x = self.pool(F.relu(x))
        x = self.conv3(x)
        x = self.BatchNorm3(x)
        x = self.pool(F.relu(x))
        x = self.conv4(x)
        x = self.BatchNorm5(x)
        x = self.pool(F.relu(x))
        x = self.conv5(x)
        x = self.BatchNorm6(x)
        x = self.pool(F.relu(x))
        x = self.dropout(x)
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = self.fc1(x)
        x = self.BatchNorm4(x)
        x = F.relu(x)
        x = self.fc2(x)
        return x

#net = Net()
#print(net)

class TransferNet(nn.Module):
    def __init__(self, architecture):
        super(TransferNet, self).__init__()
        self.arch = architecture
        if 'EfficientNet' in str(arch.__class__):   
            self.arch._fc = nn.Linear(in_features=1408, out_features=500, bias=True)
            self.dropout1 = nn.Dropout(0.25)
            
        self.output = nn.Linear(500, 1)
        
    def forward(self, images):
        """
        Since BCEWithLogitsLoss uses Sigmoid we don't use sigmoid in forward propagation.
        """
        x = images
        features = self.arch(x)
        features = self.dropout1(features)
        output = self.output(features)
        
        return output

def get_transforms(mean,std,train=False,minority=False,val=False,test=False):
    
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees= [-10,10]),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.ColorJitter(brightness=[0.8,1.2], contrast=[0.8,1.2], saturation=[0.8,1.2]),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean,std=std)
    ])
    val_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=mean,std=std)
    ])
    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=mean,std=std)
    ])
    if train == True:
        return train_transform
    if val == True:
        return val_transform
    if test == True:
        return test_transform
    if minority == True:
        return minority_transform

def training(model,train_loader,valid_loader,train_df,validation_df,model_path,epochs,es_patience,criterion,optimizer,scheduler,best_score):
    training_loss_history=[]  
    training_accuracy_history=[]  
    validation_loss_history=[]  
    validation_accuracy_history=[] 


    patience = es_patience
    Total_start_time = time.time()  
    model.to(device)

    for epoch in range(epochs):

        start_time = time.time()
        correct = 0
        running_loss = 0
        model.train()

        for images, labels in train_loader:


            images, labels = images.to(device), labels.to(device)


            optimizer.zero_grad()

            output = model(images) 
            loss = criterion(output, labels.view(-1,1))  
            loss.backward()
            optimizer.step()

            # Training loss
            running_loss += loss.item()

            # Number of correct training predictions and training accuracy
            train_prediction = torch.round(torch.sigmoid(output))

            correct += (train_prediction.cpu() == labels.cpu().unsqueeze(1)).sum().item()

        train_acc = correct / len(train_df) #+len(minority_df))


        #Validation:        
        model.eval()
        predictions=[]            
        # Turn off gradients for validation prediction
        with torch.no_grad():

            validation_loss = 0
            validation_correct = 0

            for val_images, val_labels in valid_loader:


                val_images, val_labels = val_images.to(device), val_labels.to(device)


                val_output = model(val_images)
                validation_loss += (criterion(val_output, val_labels.view(-1,1))).item() 
                val_pred = torch.sigmoid(val_output)
                validation_correct += (torch.round(val_pred).cpu() == val_labels.cpu().unsqueeze(1)).sum().item()

                predictions.append(val_pred.cpu())
            pred=np.vstack(predictions).ravel()
            val_accuracy = validation_correct/len(validation_df)

            training_time = str(datetime.timedelta(seconds=time.time() - start_time))[:7]

            print("Epoch: {}/{}.. ".format(epoch+1, epochs),
                  "Training Loss: {:.3f}.. ".format(running_loss/len(train_loader)),
                  "Training Accuracy: {:.3f}..".format(train_acc),
                  "Validation Loss: {:.3f}.. ".format(validation_loss/len(valid_loader)),
                  "Validation Accuracy: {:.3f}".format(val_accuracy),
                  "Training Time: {}".format( training_time))


            scheduler.step(val_accuracy)    
            if val_accuracy >= best_score:
                best_score = val_accuracy
                patience = es_patience  
                torch.save(model, model_path)  # Save the current best model
            else:
                patience -= 1
                if patience == 0:
                    print('Ended with Early Stopping. Best Validation Accuracy: {:.3f}'.format(best_score))
                    break

        training_loss_history.append(running_loss)  
        training_accuracy_history.append(train_acc*100)    
        validation_loss_history.append(validation_loss)  
        validation_accuracy_history.append(val_accuracy*100)


    total_training_time = str(datetime.timedelta(seconds=time.time() - Total_start_time  ))[:7]                  
    print("Total Training Time: {}".format(total_training_time))
    return model,training_loss_history,training_accuracy_history,validation_loss_history,validation_accuracy_history

def accuracy_plots(training_loss_history,training_accuracy_history,validation_loss_history,validation_accuracy_history):
    fig = plt.figure(figsize=(16, 6))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    ax1.plot(training_loss_history, label= 'Training Loss')  
    ax1.plot(validation_loss_history,label='Validation Loss')
    ax1.set_title("Loss Plot")
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Loss')
    ax1.legend()

    ax2.plot(training_accuracy_history,label='Training Accuracy')  
    ax2.plot(validation_accuracy_history,label='Validation accuracy')
    ax2.set_title("Accuracy Plot")
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Accuracy')
    ax2.legend()

plt.show()

def test_statistics(model,model_path,device,test_loader,test_df):
    model = torch.load(model_path)
    model.eval()
    model.to(device)
    test_preds=[]
    test_correct = 0
    with torch.no_grad():
        for test_images, test_labels in test_loader:
            test_images, test_labels = test_images.to(device), test_labels.to(device)
            test_output = model(test_images)
            test_pred = torch.sigmoid(test_output)  
            test_correct += (torch.round(test_pred).cpu() == test_labels.cpu().unsqueeze(1)).sum().item()
            test_preds.append(test_pred.cpu())   
        test_pred=np.vstack(test_preds).ravel()
        test_pred2 = torch.tensor(test_pred)
        test_accuracy = test_correct/len(test_df)
        test_auc_score = roc_auc_score(test_df['target'].values, test_pred)  
    print("Test Accuracy: {}".format(test_accuracy*100))    
    print("Test AUC Score: {:.3f}".format(test_auc_score))
    return test_pred2,test_accuracy

def get_confusion_matrix(test_df,test_pred_torch,test_accuracy):
    test = test_df['target']
    pred = torch.round(test_pred_torch)
    cm = confusion_matrix(test, pred)
    cm_df = pd.DataFrame(cm,index = ['Benign','Malignant'], columns = ['Benign','Malignant'])
    plt.figure(figsize=(6,4))
    sns.heatmap(cm_df, annot=True)
    plt.title('Confusion Matrix \nAccuracy:{0:.3f}'.format(test_accuracy))
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()

"""## Undersampling 
Since the data is imbalanced, we undersample the data, we take equal number of patients with melanoma and without melanoma for training. Thus reducing the majority class.
"""

train_df = pd.read_csv("/content/archive-2/train.csv")
train_df.head()

df_disease_patients = train_df[train_df["patient_id"].isin(list(with_disease["patient_id"].unique()))]
df_disease_patients.shape

df_non_disease_patients = train_df[train_df["patient_id"].isin(without_disease)]
df_non_disease_patients = df_non_disease_patients.head(len(df_disease_patients))
df_non_disease_patients.shape

df = pd.concat([df_disease_patients,df_non_disease_patients])
df.shape

train_img_dir = '/content/archive-2/train/'

df.head()

intermediate_size=0.20
test_size = 0.50

train, interim = train_test_split(df, stratify=df.target, test_size = intermediate_size, random_state=42)
test, valid = train_test_split(interim, stratify=interim.target, test_size = test_size, random_state=42)

train_df=pd.DataFrame(train)
validation_df=pd.DataFrame(valid)
test_df = pd.DataFrame(test)

print(len(train_df))
print(len(validation_df))
print(len(test_df))
print(train_df.target.value_counts())
print(validation_df.target.value_counts())
print(test_df.target.value_counts())

"""### FOR EFFICIENTNET-B2 MODEL"""

mean = [0.485, 0.456, 0.406] #This mean is taken for the imagenet dataset during pretraining
std = [0.229, 0.224, 0.225] #This std is taken for the imagenet dataset during pretraining
training_dataset = MelanomaDataset(df = train_df,
                                 img_dir = train_img_dir, 
                                 train = True,
                                 transforms = get_transforms(mean,std,train=True))

validation_dataset = MelanomaDataset(df = validation_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,val=True))

test_dataset = MelanomaDataset(df = test_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,test=True))

train_df.target.value_counts()

"""Weight Random Sampler is used to tackle the imbalance issue in the data."""

class_weights = [1/train_df.target.value_counts()[0],1/train_df.target.value_counts()[1]]
sample_weights = [0]*len(training_dataset)
for idx, (data,label) in enumerate(training_dataset):
    class_weight = class_weights[int(label)]
    sample_weights[idx] = class_weight
weighted_sampler = WeightedRandomSampler(sample_weights,num_samples=len(sample_weights),replacement=True)

"""In Train_Loader shuffle is False because here weights are used for sampling the samples i.e. there is random sampling using weight as probabilities."""

# Using the image datasets with the transforms, defining the dataloaders
#train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=32, num_workers=4, shuffle=True)
train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=32,sampler = weighted_sampler, num_workers=4, shuffle=False)
valid_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=16, shuffle = False)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle = False)

print(len(train_loader))
print(len(valid_loader))
print(len(test_loader))

arch = EfficientNet.from_pretrained('efficientnet-b2')
model = TransferNet(architecture=arch)  
model = model.to(device)

#print(model)

# Empty variable to be stored with best validation accuracy
best_score = 0
# Path and filename to save model to
model_path = f'melanoma_{best_score}.pth'  
# Number of Epochs
epochs = 10
# Early stopping if no change in accuracy
es_patience = 3
# Loss Function
criterion = nn.BCEWithLogitsLoss()
# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.0006) 
# Scheduler
scheduler = ReduceLROnPlateau(optimizer=optimizer, mode='max', patience=1, verbose=True, factor=0.4)

model,train_loss,train_accuracy,valid_loss,valid_accuracy = training(model,train_loader,valid_loader,train_df,validation_df,model_path,epochs,es_patience,criterion,optimizer,scheduler,best_score)
accuracy_plots(train_loss,train_accuracy,valid_loss,valid_accuracy)

test_pred_torch,test_accuracy = test_statistics(model,model_path,device,test_loader,test_df)
get_confusion_matrix(test_df,test_pred_torch,test_accuracy)

test = test_df['target']
pred = torch.round(test_pred_torch)
print(classification_report(test,pred))

"""### Custom Network"""

model = Net()  
model = model.to(device)

mean = [0.5, 0.5, 0.5]
std = [0.5, 0.5, 0.5]
training_dataset = MelanomaDataset(df = train_df,
                                 img_dir = train_img_dir, 
                                 train = True,
                                 transforms = get_transforms(mean,std,train=True))

validation_dataset = MelanomaDataset(df = validation_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,val=True))

test_dataset = MelanomaDataset(df = test_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,test=True))

train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=32,sampler = weighted_sampler, num_workers=4, shuffle=False)
valid_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=16, shuffle = False)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle = False)

# Empty variable to be stored with best validation accuracy
best_score = 0
# Path and filename to save model to
model_path = f'melanoma_{best_score}.pth'  
# Number of Epochs
epochs = 20
# Early stopping if no change in accuracy
es_patience = 5
# Loss Function
criterion = nn.BCEWithLogitsLoss()
# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.0005) 
# Scheduler
scheduler = ReduceLROnPlateau(optimizer=optimizer, mode='max', patience=1, verbose=True, factor=0.4)

model,train_loss,train_accuracy,valid_loss,valid_accuracy = training(model,train_loader,valid_loader,train_df,validation_df,model_path,epochs,es_patience,criterion,optimizer,scheduler,best_score)
accuracy_plots(train_loss,train_accuracy,valid_loss,valid_accuracy)

test_pred_torch,test_accuracy = test_statistics(model,model_path,device,test_loader,test_df)
get_confusion_matrix(test_df,test_pred_torch,test_accuracy)

test = test_df['target']
pred = torch.round(test_pred_torch)
print(classification_report(test,pred))

"""# Oversampling the Minority Class
Here we use another dataset where we have more images in the minor class. These images are added from external sources from the web. The image size in this dataset is also 256x256 as our previous dataset.
"""

df = pd.read_csv('/content/archive-3/train_concat.csv')
train_img_dir = '/content/archive-3/train/train/'

intermediate_size=0.20
test_size = 0.50

train, interim = train_test_split(df, stratify=df.target, test_size = intermediate_size, random_state=42)
test, valid = train_test_split(interim, stratify=interim.target, test_size = test_size, random_state=42)

train_df=pd.DataFrame(train)
validation_df=pd.DataFrame(valid)
test_df = pd.DataFrame(test)

print(len(train_df))
print(len(validation_df))
print(len(test_df))
print(train_df.target.value_counts())
print(validation_df.target.value_counts())
print(test_df.target.value_counts())

mean = [0.5, 0.5, 0.5]
std = [0.5, 0.5, 0.5]
training_dataset = MelanomaDataset(df = train_df,
                                 img_dir = train_img_dir, 
                                 train = True,
                                 transforms = get_transforms(mean,std,train=True))

validation_dataset = MelanomaDataset(df = validation_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,val=True))

test_dataset = MelanomaDataset(df = test_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,test=True))

class_weights = [1/train_df.target.value_counts()[0],1/train_df.target.value_counts()[1]]
sample_weights = [0]*len(training_dataset)
for idx, (data,label) in enumerate(training_dataset):
    class_weight = class_weights[int(label)]
    sample_weights[idx] = class_weight
weighted_sampler = WeightedRandomSampler(
    sample_weights,
    num_samples=len(sample_weights),
    replacement=True
)

"""### Custom Network"""

model = Net()  
model = model.to(device)

train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=32,sampler = weighted_sampler, num_workers=4, shuffle=False)
valid_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=16, shuffle = False)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle = False)

# Empty variable to be stored with best validation accuracy
best_score = 0
# Path and filename to save model to
model_path = f'melanoma_{best_score}.pth'  
# Number of Epochs
epochs = 10
# Early stopping if no change in accuracy
es_patience = 5
# Loss Function
criterion = nn.BCEWithLogitsLoss()
# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.0005) 
# Scheduler
scheduler = ReduceLROnPlateau(optimizer=optimizer, mode='max', patience=1, verbose=True, factor=0.4)

model,train_loss,train_accuracy,valid_loss,valid_accuracy = training(model,train_loader,valid_loader,train_df,validation_df,model_path,epochs,es_patience,criterion,optimizer,scheduler,best_score)
accuracy_plots(train_loss,train_accuracy,valid_loss,valid_accuracy)

test_pred_torch,test_accuracy = test_statistics(model,model_path,device,test_loader,test_df)
get_confusion_matrix(test_df,test_pred_torch,test_accuracy)

test = test_df['target']
pred = torch.round(test_pred_torch)
print(classification_report(test,pred))

"""### EfficientNet-B2"""

arch = EfficientNet.from_pretrained('efficientnet-b2')
model = TransferNet(architecture=arch)  
model = model.to(device)

mean = [0.485, 0.456, 0.406]
std = [0.229, 0.224, 0.225]
training_dataset = MelanomaDataset(df = train_df,
                                 img_dir = train_img_dir, 
                                 train = True,
                                 transforms = get_transforms(mean,std,train=True))

validation_dataset = MelanomaDataset(df = validation_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,val=True))

test_dataset = MelanomaDataset(df = test_df,
                                   img_dir = train_img_dir, 
                                   train = True,
                                   transforms = get_transforms(mean,std,test=True))

train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=32,sampler = weighted_sampler, num_workers=4, shuffle=False)
valid_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=16, shuffle = False)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle = False)

# Empty variable to be stored with best validation accuracy
best_score = 0
# Path and filename to save model to
model_path = f'melanoma_{best_score}.pth'  
# Number of Epochs
epochs = 5
# Early stopping if no change in accuracy
es_patience = 3
# Loss Function
criterion = nn.BCEWithLogitsLoss()
# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.0006) 
# Scheduler
scheduler = ReduceLROnPlateau(optimizer=optimizer, mode='max', patience=1, verbose=True, factor=0.4)

model,train_loss,train_accuracy,valid_loss,valid_accuracy = training(model,train_loader,valid_loader,train_df,validation_df,model_path,epochs,es_patience,criterion,optimizer,scheduler,best_score)
accuracy_plots(train_loss,train_accuracy,valid_loss,valid_accuracy)

"""### The Colab limit reached at this point. We ran the this last model in a separate file and we have published the results in the main report."""

test_pred_torch,test_accuracy = test_statistics(model,model_path,device,test_loader,test_df)
get_confusion_matrix(test_df,test_pred_torch,test_accuracy)

test = test_df['target']
pred = torch.round(test_pred_torch)
print(classification_report(test,pred))
