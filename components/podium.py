import html
import streamlit as st
from utils.formatting import euro
from utils.images import image_data_uri,player_photo


def _competitor(player, place):
    photo=player_photo(player["photo_path"])
    image=f'<img src="{image_data_uri(photo)}" alt="{html.escape(player["first_name"])}">' if photo else '<div class="podium-avatar">♟</div>'
    medal={1:"🥇",2:"🥈",3:"🥉"}[place]
    return f'''<article class="podium-competitor place-{place}">
      <div class="podium-medal">{medal}</div>
      <div class="podium-player-photo">{image}</div>
      <div class="podium-identity">
        <b>{html.escape(player["first_name"])} {html.escape(player["last_name"])}</b>
        <span>#{player["jersey_number"]} · {euro(player["total"])}</span>
      </div>
      <div class="podium-plinth"><i>{place}</i></div>
    </article>'''


def podium(players):
    if len(players)<3:
        return
    # Ordre visuel classique : deuxième, champion, troisième.
    markup=_competitor(players[1],2)+_competitor(players[0],1)+_competitor(players[2],3)
    st.markdown(f'<section class="phoenix-podium"><div class="podium-glow"></div>{markup}</section>',unsafe_allow_html=True)
