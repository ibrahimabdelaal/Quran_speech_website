from flask import render_template
from app import app
from app.models import Surah, Verse

@app.route('/')
def index():
    print("hereeeeeeee")
    #surahs = Surah.query.all()
    return render_template('index.html')#,surahs=surahs)

@app.route('/surah/<int:surah_id>')
def surah(surah_id):
    surah = Surah.query.get_or_404(surah_id)
    verses = Verse.query.filter_by(surah_id=surah.id).all()
    return render_template('surah.html', surah=surah, verses=verses)
