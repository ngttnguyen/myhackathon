
# Ref: https://towardsdatascience.com/data-apps-with-pythons-streamlit-b14aaca7d083

#/app.py
import streamlit as st #pip install streamlit
import pandas as pd
import numpy as np

from datetime import date
from datetime import time
import datetime as dt

# Initial setup
st.set_page_config(layout="wide")

# Load data
basket_df = pd.read_excel("streamlit_data/basket_output.xlsx")
listen_free_user_df = pd.read_csv("streamlit_data/listen_free_user_df.csv")
hv_convert_content_df = pd.read_excel("streamlit_data/hv_convert_content.xlsx")
listen_free_user_df["Listening Date"]=listen_free_user_df["Listening Date"].astype("datetime64[ns]")

## Function suggest together_playlists base on basket analysis
def define_hardPlaylist(user_id, listen_free_user_df):
    df = listen_free_user_df[listen_free_user_df["UserID (FK)"]==user_id]
    bottom_date = df["Listening Date"].max() -dt.timedelta(days = 14)
    playlist = df[df["Listening Date"]>bottom_date]
    playlist_summary=playlist.groupby(["UserID (FK)","PlaylistID (PK)","Playlist Name"]).agg(
    {"Actual Duration (min)":["sum"]}).reset_index()
    playlist_summary.columns=["UserID","PlaylistID","PlaylistName","TotalDuration"]
    hard_playlist= playlist_summary.loc[playlist_summary["TotalDuration"].idxmax(),["PlaylistID","PlaylistName"]]
    return hard_playlist[1]

def suggest_together_playlists(user_id,listen_free_user_df):
    playlist = define_hardPlaylist(user_id, listen_free_user_df)
    together_playlists = basket_df[basket_df["antecedents"] == playlist]["next playlist"].to_list()
    if len(together_playlists)>1:
        return (together_playlists[0].split(","))
    else:
        return (together_playlists)

def extract_high_value(x,high_value_user):
#     high_value_user = listening_df[listening_df['Value Rank'] == 'High Value']
    high_value_user_filter = high_value_user[high_value_user['UserID (FK)'] == x]
    last_listening = high_value_user_filter.groupby(by='UserID (FK)')['Listening Date'].max().reset_index()
    last_listening.columns = ['UserID (FK)','Last Listening Date']
    test = pd.merge(high_value_user_filter, last_listening, how='left', on= 'UserID (FK)')
    test['Last Listening Date'] = test['Last Listening Date'].astype('datetime64')
    test['time window'] = (test['Last Listening Date'] - test['Listening Date']).dt.days
    test = test[test['time window'] <= 14]
    test = test.groupby(by=['UserID (FK)', 'Sub Category'])['PlaylistID (PK)'].count().reset_index()
    test.columns = ['UserID (FK)', 'Sub Category', 'Listening Count']
    test = test[test['Listening Count'] == test['Listening Count'].max()]
    test = pd.merge(test, hv_convert_content_df[['PlaylistID','PlaylistName', 'Category', 'SubCategory' , 'AvgDuration']], how='left', left_on='Sub Category', right_on = 'SubCategory' )
    lst = test['PlaylistName'].tolist()
    
    return lst

def recommend_playlists(user_id, listen_free_user_df):
    lst1 = extract_high_value(user_id,listen_free_user_df)
    lst2 = suggest_together_playlists(user_id,listen_free_user_df)
    lst3 = lst1 + lst2
    newlist=[ii for n,ii in enumerate(lst3) if ii not in lst3[:n]]
    
    return ((newlist[:3]+newlist[-3:]) if len(newlist)>6 else newlist )

def recommend_forFreeUser():
    
    clusters = listen_free_user_df.groupby(["MainCluster_ID","MainCluster_Description"]).agg({"UserID (FK)":"count"}).reset_index()
    clusters.columns=["MainCluster_ID","MainCluster_Description","#"]
    clusters=clusters.sort_values(by=["MainCluster_ID"],ascending=False) 
    
    ## Select Box:
    cluster = st.sidebar.selectbox("Choose cluster for free users:",options=clusters["MainCluster_Description"].tolist())
        
    ## Slider
    max_val = clusters[clusters.MainCluster_Description == cluster]["#"].tolist()[0]
    user_num = st.sidebar.slider("Number of users for recommending:", min_value= 0, max_value= max_val, value=int(max_val/2), step=int(max_val/50))
    ## Get list users
    users_lst = listen_free_user_df[listen_free_user_df["MainCluster_Description"]==cluster]["UserID (FK)"].unique().tolist()
    users_lst = users_lst[:user_num]

    ##     Recommend button
    
    if st.sidebar.button("Get Recommendation Playlist"):
        recomemend_lst = {}
        for user in users_lst:
            recomemend_lst[user] = recommend_playlists(user,listen_free_user_df) 
        recomemend_df = pd.DataFrame()
        recomemend_df["User_ID"]=recomemend_lst.keys()
        recomemend_df["RecommendPlaylists"]=recomemend_lst.values()
        
        st.write(" The bundle of 20 highly recommended Playlists:")
        st.table(data=recomemend_df.iloc[:20])
        st.markdown(get_table_download_link_csv(recomemend_df), unsafe_allow_html=True)

        
def get_table_download_link_csv(df):
    csv = df.to_csv().encode()
    # b64 = base64.b64encode(csv).decode()
    # href = f'<a href="data:file/csv;base64,{b64}" download="recommendPlaylist.csv" target="_blank">Download csv file</a>'
    href = f'<a href="data:file/csv" download="recommendPlaylist.csv" target="_blank">Download csv file</a>'
    return href
        
    
def main():
    
    st.title('Voiz: Recommendation Playlist for Free Users')
    recommend_forFreeUser()
    

main()

## Run: streamlit run hackathon_voiz_streamlit.py