import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBClassifier
import warnings
import pickle
warnings.filterwarnings('ignore')

data = pd.read_csv("phishing.csv")
data.head()
data.shape
data.info()
data = data.drop(['Index'],axis = 1)
data.describe().T


#Correlation heatmap
#plt.figure(figsize=(15,15))
#sns.heatmap(data.corr(), annot=True)
#plt.show()

# Splitting the dataset into dependant and independant fetature
#X = data.drop(["class"],axis =1)
#y = data["class"]
y = data["class"].replace(-1, 0)  # XGBoost expects 0/1 instead of -1/1
X = data.drop(["class"], axis=1)
print(y.value_counts())


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)
#X_train.shape, y_train.shape, X_test.shape, y_test.shape

# Creating holders to store the model performance results
ML_Model = []
accuracy = []
f1_score = []
recall = []
precision = []

#function to call for storing the results
def storeResults(model, a,b,c,d):
  ML_Model.append(model)
  accuracy.append(round(a, 3))
  f1_score.append(round(b, 3))
  recall.append(round(c, 3))
  precision.append(round(d, 3))

"""
training_accuracy = []
test_accuracy = []
# try max_depth from 1 to 30
depth = range(1, 30)
for n in depth:
  tree_test = DecisionTreeClassifier(max_depth=n)
  tree_test.fit(X_train, y_train)
  training_accuracy.append(tree_test.score(X_train, y_train))
  test_accuracy.append(tree_test.score(X_test, y_test))

# plotting the training & testing accuracy for max_depth from 1 to 30
plt.plot(depth, training_accuracy, label="training accuracy")
plt.plot(depth, test_accuracy, label="test accuracy")
plt.ylabel("Accuracy")
plt.xlabel("max_depth")
plt.legend()
"""
# Decision Tree Classifier model
tree = DecisionTreeClassifier(max_depth=30)
tree.fit(X_train, y_train)
y_train_tree = tree.predict(X_train)
y_test_tree = tree.predict(X_test)
#computing the classification report of the model
acc_train_tree = metrics.accuracy_score(y_train,y_train_tree)
acc_test_tree = metrics.accuracy_score(y_test,y_test_tree)
#print("Decision Tree : Accuracy on training Data: {:.3f}".format(acc_train_tree))
#print("Decision Tree : Accuracy on test Data: {:.3f}".format(acc_test_tree))
f1_score_train_tree = metrics.f1_score(y_train,y_train_tree)
f1_score_test_tree = metrics.f1_score(y_test,y_test_tree)
#print("Decision Tree : f1_score on training Data: {:.3f}".format(f1_score_train_tree))
#print("Decision Tree : f1_score on test Data: {:.3f}".format(f1_score_test_tree))
recall_score_train_tree = metrics.recall_score(y_train,y_train_tree)
recall_score_test_tree = metrics.recall_score(y_test,y_test_tree)
#print("Decision Tree : Recall on training Data: {:.3f}".format(recall_score_train_tree))
#print("Decision Tree : Recall on test Data: {:.3f}".format(recall_score_test_tree))
precision_score_train_tree = metrics.precision_score(y_train,y_train_tree)
precision_score_test_tree = metrics.precision_score(y_test,y_test_tree)
#print("Decision Tree : precision on training Data: {:.3f}".format(precision_score_train_tree))
#print("Decision Tree : precision on test Data: {:.3f}".format(precision_score_test_tree))
#print(metrics.classification_report(y_test, y_test_tree))
storeResults('Decision Tree',acc_test_tree,f1_score_test_tree,recall_score_train_tree,precision_score_train_tree)


"""
training_accuracy = []
test_accuracy = []
# try max_depth from 1 to 20
depth = range(1,20)
for n in depth:
    forest_test =  RandomForestClassifier(n_estimators=n)
    forest_test.fit(X_train, y_train)
    training_accuracy.append(forest_test.score(X_train, y_train))
    test_accuracy.append(forest_test.score(X_test, y_test))
#plotting the training & testing accuracy for n_estimators from 1 to 20
plt.figure(figsize=None)
plt.plot(depth, training_accuracy, label="training accuracy")
plt.plot(depth, test_accuracy, label="test accuracy")
plt.ylabel("Accuracy")  
plt.xlabel("n_estimators")
plt.legend()
"""
# Random Forest Classifier Model
forest = RandomForestClassifier(n_estimators=10)
forest.fit(X_train,y_train)
#predicting the target value from the model for the samples
y_train_forest = forest.predict(X_train)
y_test_forest = forest.predict(X_test)
#computing the accuracy, f1_score, Recall, precision of the model performance
acc_train_forest = metrics.accuracy_score(y_train,y_train_forest)
acc_test_forest = metrics.accuracy_score(y_test,y_test_forest)
#print("Random Forest : Accuracy on training Data: {:.3f}".format(acc_train_forest))
#print("Random Forest : Accuracy on test Data: {:.3f}".format(acc_test_forest))
f1_score_train_forest = metrics.f1_score(y_train,y_train_forest)
f1_score_test_forest = metrics.f1_score(y_test,y_test_forest)
#print("Random Forest : f1_score on training Data: {:.3f}".format(f1_score_train_forest))
#print("Random Forest : f1_score on test Data: {:.3f}".format(f1_score_test_forest))
recall_score_train_forest = metrics.recall_score(y_train,y_train_forest)
recall_score_test_forest = metrics.recall_score(y_test,y_test_forest)
#print("Random Forest : Recall on training Data: {:.3f}".format(recall_score_train_forest))
#print("Random Forest : Recall on test Data: {:.3f}".format(recall_score_test_forest))
precision_score_train_forest = metrics.precision_score(y_train,y_train_forest)
precision_score_test_forest = metrics.precision_score(y_test,y_test_tree)
#print("Random Forest : precision on training Data: {:.3f}".format(precision_score_train_forest))
#print("Random Forest : precision on test Data: {:.3f}".format(precision_score_test_forest))
storeResults('Random Forest',acc_test_forest,f1_score_test_forest,recall_score_train_forest,precision_score_train_forest)



#  XGBoost Classifier Model
xgb = XGBClassifier()
xgb.fit(X_train,y_train)
#predicting the target value from the model for the samples
y_train_xgb = xgb.predict(X_train)
y_test_xgb = xgb.predict(X_test)
#computing the accuracy, f1_score, Recall, precision of the model performance
acc_train_xgb = metrics.accuracy_score(y_train,y_train_xgb)
acc_test_xgb = metrics.accuracy_score(y_test,y_test_xgb)
#print("XGBoost Classifier : Accuracy on training Data: {:.3f}".format(acc_train_xgb))
#print("XGBoost Classifier : Accuracy on test Data: {:.3f}".format(acc_test_xgb))
f1_score_train_xgb = metrics.f1_score(y_train,y_train_xgb)
f1_score_test_xgb = metrics.f1_score(y_test,y_test_xgb)
#print("XGBoost Classifier : f1_score on training Data: {:.3f}".format(f1_score_train_xgb))
#print("XGBoost Classifier : f1_score on test Data: {:.3f}".format(f1_score_test_xgb))
recall_score_train_xgb = metrics.recall_score(y_train,y_train_xgb)
recall_score_test_xgb = metrics.recall_score(y_test,y_test_xgb)
#print("XGBoost Classifier : Recall on training Data: {:.3f}".format(recall_score_train_xgb))
#print("XGBoost Classifier : Recall on test Data: {:.3f}".format(recall_score_train_xgb))
precision_score_train_xgb = metrics.precision_score(y_train,y_train_xgb)
precision_score_test_xgb = metrics.precision_score(y_test,y_test_xgb)
#print("XGBoost Classifier : precision on training Data: {:.3f}".format(precision_score_train_xgb))
#print("XGBoost Classifier : precision on test Data: {:.3f}".format(precision_score_train_xgb))
storeResults('XGBoost Classifier',acc_test_xgb,f1_score_test_xgb,recall_score_train_xgb,precision_score_train_xgb)



#Gradient Boosting Classifier Model
gbc = GradientBoostingClassifier(max_depth=4,learning_rate=0.7)
# fit the model
gbc.fit(X_train,y_train)
GradientBoostingClassifier(learning_rate=0.7, max_depth=4)
#predicting the target value from the model for the samples
y_train_gbc = gbc.predict(X_train)
y_test_gbc = gbc.predict(X_test)
#computing the accuracy, f1_score, Recall, precision of the model performance
acc_train_gbc = metrics.accuracy_score(y_train,y_train_gbc)
acc_test_gbc = metrics.accuracy_score(y_test,y_test_gbc)
#print("Gradient Boosting Classifier : Accuracy on training Data: {:.3f}".format(acc_train_gbc))
#print("Gradient Boosting Classifier : Accuracy on test Data: {:.3f}".format(acc_test_gbc))
f1_score_train_gbc = metrics.f1_score(y_train,y_train_gbc)
f1_score_test_gbc = metrics.f1_score(y_test,y_test_gbc)
#print("Gradient Boosting Classifier : f1_score on training Data: {:.3f}".format(f1_score_train_gbc))
#print("Gradient Boosting Classifier : f1_score on test Data: {:.3f}".format(f1_score_test_gbc))
recall_score_train_gbc = metrics.recall_score(y_train,y_train_gbc)
recall_score_test_gbc =  metrics.recall_score(y_test,y_test_gbc)
#print("Gradient Boosting Classifier : Recall on training Data: {:.3f}".format(recall_score_train_gbc))
#print("Gradient Boosting Classifier : Recall on test Data: {:.3f}".format(recall_score_test_gbc))
precision_score_train_gbc = metrics.precision_score(y_train,y_train_gbc)
precision_score_test_gbc = metrics.precision_score(y_test,y_test_gbc)
#print("Gradient Boosting Classifier : precision on training Data: {:.3f}".format(precision_score_train_gbc))
#print("Gradient Boosting Classifier : precision on test Data: {:.3f}".format(precision_score_test_gbc))
storeResults('Gradient Boosting Classifier',acc_test_gbc,f1_score_test_gbc,recall_score_train_gbc,precision_score_train_gbc)

#creating dataframe
result = pd.DataFrame({ 'ML Model' : ML_Model,
                        'Accuracy' : accuracy,
                        'f1_score' : f1_score,
                        'Recall'   : recall,
                        'Precision': precision,
                      })
print(result)
#Sorting the datafram on accuracy
sorted_result=result.sort_values(by=['Accuracy', 'f1_score'],ascending=False).reset_index(drop=True)
print("Sorted result:")
print(sorted_result)



# Saving the model
pickle.dump(gbc, open('models/phishing_model.pkl', 'wb'))
#checking the feature improtance in the model
#plt.figure(figsize=(9,7))
#n_features = X_train.shape[1]
#plt.barh(range(n_features), gbc.feature_importances_, align='center')
#plt.yticks(np.arange(n_features), X_train.columns)
#plt.title("Feature importances using permutation on full model")
#plt.xlabel("Feature importance")
#plt.ylabel("Feature")
#plt.show()