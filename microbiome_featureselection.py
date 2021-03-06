import pandas as pd
import seaborn as sns
import numpy as np
import re
import matplotlib.pyplot as plt
import scipy.spatial.distance as ssd
import csv

import sklearn.metrics as metrics
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import ElasticNetCV, ElasticNet, LogisticRegression, LogisticRegressionCV, Lasso, LassoCV
from sklearn.model_selection import train_test_split, GridSearchCV, train_test_split, cross_val_score, RepeatedKFold
from sklearn.svm import LinearSVC
from sklearn.feature_selection import SelectFromModel, VarianceThreshold, SelectKBest, chi2, GenericUnivariateSelect, f_classif, mutual_info_classif
from sklearn import preprocessing
from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier 
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, Normalizer, MinMaxScaler
from sklearn import svm
from numpy import mean, std, absolute,arange
from pandas import read_csv
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, cohen_kappa_score, make_scorer, f1_score, accuracy_score, r2_score, roc_curve

def variance_threshold_selector(data):
    #threshold=(.8 * (1 - .8))
    threshold = 0
    selector = VarianceThreshold(threshold)
    selector.fit(data)
    #data_transformed = data.loc[:, selector.get_support()]
    fs_data = data[data.columns[selector.get_support(indices=True)]]
    return fs_data.abs()

def pheno_to_numerical(data):
    # CD = 1, UC = 2, NON IBD = 3
    data = data.replace({'CD': 1, 'UC': 2, 'nonIBD':3}) 
    data = data.reset_index()
    return data

def fill_NA(data):
    #data.fillna(data.median(), inplace=True)
    original = data
    data.fillna(0)
    data = MinMaxScaler().fit_transform(data)
    data = pd.DataFrame(data, columns=original.columns)
    return data.abs()

def normalize(df):
    result = df.copy()
    for feature_name in df.columns:
        max_value = df[feature_name].max()
        min_value = df[feature_name].min()
        result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
    return result

def topfeatures_chi2(X,y, X_test):
    selector = SelectKBest(chi2, k=50)
    selector.fit(X, y)
    #transform
    X_train_fs = pd.DataFrame(selector.transform(X), columns = X.columns[selector.get_support()])
    X_test_fs = pd.DataFrame(selector.transform(X_test), columns = X_test.columns[selector.get_support()])
    #Get columns to keep and create new dataframe with those only
    #cols = selector.get_support(indices=True)
    #fs_df_new = X.iloc[:,cols]
    #X_test = X_test.iloc[:,cols]
    return X_train_fs, X_test_fs

def topfeatures_univariate(X,y, X_test):
    #ANOVA F-value between label/feature for classification tasks.
    univariate_filter = SelectKBest(f_classif, k=50)
    univariate_filter.fit(X,y)
    #Get columns to keep and create new dataframe with those only
    cols = univariate_filter.get_support(indices=True)
    fs_df_new = X.iloc[:,cols]
    univariate_filter.transform(X,y)
    X_test = univariate_filter.transform(X_test)
    X_test = pd.DataFrame(X_test)
    return fs_df_new , X_test

def pipeline_ANOVA(X_train, y_train, X_test):

    anova_filter = SelectKBest(f_classif, k=50)
    clf_anova = LinearSVC()
    anova_svm = make_pipeline(anova_filter, clf_anova)
    anova_svm.fit(X_train, y_train)
    y_pred = anova_svm.predict(X_test)
    return y_pred

def pipeline_CHI2(X_train, y_train, X_test):

    chi2_filter = SelectKBest(chi2, k=50)
    clf_chi2 = LinearSVC()
    chi2_svm = make_pipeline(chi2_filter, clf_chi2)
    chi2_svm.fit(X_train, y_train)
    y_pred = chi2_svm.predict(X_test)
    return y_pred

def pipeline_MI(X_train, y_train, X_test):

    MI_filter = SelectKBest(mutual_info_classif, k=50)
    clf_MI = LinearSVC()
    MI_svm = make_pipeline(MI_filter, clf_MI)
    MI_svm.fit(X_train, y_train)
    y_pred = MI_svm.predict(X_test)
    return y_pred

def lasso_classifier(X_features, X_test, y):
    #X_features es el output de haber usado chi2 o univariate
    model1 = LassoCV(cv=10, fit_intercept=True,  normalize=False, n_jobs=-1)
    model1.fit(X_features, y)
    #X_test = model1.transform(X_test)
    y_hat = model1.predict(X_test)
    return y_hat

def lsvc(x,y):
    # The smaller C, the stronger the regularization.
    # The more regularization, the more sparsity.
    
    lsvc = LinearSVC(C=0.01).fit(x, y)
    model = SelectFromModel(lsvc, prefit=True)
    X_train = model.transform(x)
    #X_test = model.transform(x2)
    return X_train

def evaluate_model(X, y):
    cv = KFold(n_splits=10, random_state=1, shuffle=True)
    scores = cross_val_score(model, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
    # report performance
    return print('Accuracy: %.3f (%.3f)' % (mean(scores), std(scores)))

def get_fs_columns(data, original_df):

    listfs = data.columns
    filtered_data = original_df[np.intersect1d(original_df.columns, listfs)]

    return filtered_data

def get_fs_columns_II(listfs, original_df):

    filtered_data = original_df[np.intersect1d(original_df.columns, listfs)]

    return filtered_data

def feature_importance(X, y, X_t):
    #X_train, y_train
    feature_names = [f"feature {i}" for i in range(X.shape[1])]
    forest = RandomForestClassifier(random_state=0)
    forest.fit(X, y)
    result = forest.predict(X_t)

    return result, feature_names, forest

def random_forest_clf(X_train, y_train, X_test, y_test):

    n_estimators_RF = [50, 100, 250, 500, 1000]
    max_features_RF = [None]
    parameters_RF = {'n_estimators': n_estimators_RF,
                      'max_features': max_features_RF}

    RF_model = RandomForestClassifier(max_depth=None,
                                  min_samples_split=2, random_state=0)
    RF_clf = GridSearchCV(RF_model, parameters_RF, cv=5, scoring="accuracy")

    RF_clf.fit(X_train, y_train)

    y_prob = RF_clf.predict_proba(X_test)
    #Print Best Model
    RF_model = RF_clf.best_estimator_
    print(RF_model)

    RF_predictions = RF_model.predict(X_test) 
  
    # create and return confusion matrix 
    cm_RF = confusion_matrix(y_test, RF_predictions)
    return cm_RF, RF_clf, y_prob

"""BACKUP:


"""

def normalize_dataset(df):
    #log10 transform
    df = df.apply(np.log10)
    # robust standardization
    df = df.apply(lambda x: (x-x.median())/x.std())
    # impue missing values with minimum
    df = df.fillna(df.min())
    return df
