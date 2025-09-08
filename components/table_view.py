# components/table_view.py
import streamlit as st
import pandas as pd

def display_dataframe(df: pd.DataFrame):
    st.dataframe(df)