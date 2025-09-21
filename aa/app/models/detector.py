import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_and_detect():
    np.random.seed(42)
    data = pd.DataFrame({
        "col1": np.random.rand(500),
        "col2": np.random.rand(500),
        "col3": np.random.rand(500),
        "col4": np.random.rand(500),
        "col5": np.random.rand(500),
    })
    labels = np.random.choice([0,1], size=500)

    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)
    clf = RandomForestClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    importances = clf.feature_importances_
    top_cols = X_train.columns[np.argsort(importances)[::-1][:3]]
    return acc, list(top_cols)
