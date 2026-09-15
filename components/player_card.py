import streamlit as st
from utils.formatting import euro
from utils.images import image_data_uri,player_photo
from utils.translations import t

def card(player, key, lang="FR", compact=False):
    photo=player_photo(player["photo_path"])
    with st.container(border=True):
        st.markdown(f'<div class="jersey">#{player["jersey_number"]}</div>',unsafe_allow_html=True)
        if photo:
            st.markdown(f'<div class="player-visual"><img src="{image_data_uri(photo)}" alt="{player["first_name"]} {player["last_name"]}"></div>',unsafe_allow_html=True)
        else: st.markdown('<div class="avatar">♟</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="player-name">{player["first_name"]}<br><b>{player["last_name"]}</b></div><div class="player-money">{euro(player.get("total",0))} <small>· {t("remaining",lang).lower()} {euro(player.get("remaining",0))}</small></div>',unsafe_allow_html=True)
        if st.button(t("view_profile",lang),key=key,width="stretch"):
            st.session_state.selected_player=player["id"]; st.session_state.page="profile"; st.rerun()
