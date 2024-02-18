# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import ast
import logging
import os
import sys
from logging import FileHandler, Formatter

import babel
import dateutil.parser
from flask import flash, redirect, render_template, request, url_for
from flask_migrate import Migrate

from forms import *
from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []

    results = Venue.query.distinct(Venue.city, Venue.state).all()

    for x in results:
        venues = Venue.query.filter_by(city=x.city, state=x.state).all()

        venueList = []
        for v in venues:
            shows = Show.query.filter(
                Show.venue_id == v.id, Show.start_time >= datetime.now()
            ).all()

            venueList.append(
                {
                    "id": v.id,
                    "name": v.name,
                    "num_upcoming_shows": len(shows),
                }
            )

        data.append({"city": x.city, "state": x.state, "venues": venueList})

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "").strip()

    venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()

    list = []

    for v in venues:
        shows = Show.query.filter(
            Show.venue_id == v.id, Show.start_time >= datetime.now()
        ).all()

        list.append(
            {
                "id": v.id,
                "name": v.name,
                "num_upcoming_shows": len(shows),
            }
        )

    response = {
        "count": len(venues),
        "data": list,
    }

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    result = Venue.query.get(venue_id)

    converted_list = ast.literal_eval(result.genres)

    shows = Show.query.filter(Show.venue_id == venue_id).all()
    past_shows = []
    upcoming_shows = []
    for s in shows:
        if s.start_time > datetime.now():
            upcoming_shows.append(
                {
                    "artist_image_link": s.artist.image_link,
                    "artist_id": s.artist_id,
                    "artist_name": s.artist.name,
                    "start_time": str(s.start_time),
                }
            )
        else:
            past_shows.append(
                {
                    "artist_image_link": s.artist.image_link,
                    "artist_id": s.artist_id,
                    "artist_name": s.artist.name,
                    "start_time": str(s.start_time),
                }
            )

    data = {
        "id": result.id,
        "name": result.name,
        "genres": converted_list,
        "city": result.city,
        "state": result.state,
        "address": result.address,
        "phone": result.phone,
        "website": result.website_link,
        "facebook_link": result.facebook_link,
        "seeking_talent": result.seeking_talent,
        "seeking_description": result.seeking_description,
        "image_link": result.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    form = VenueForm(request.form)

    if form.validate_on_submit():
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=str(form.genres.data),
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
        )

        try:
            db.session.add(venue)
            db.session.commit()
            flash("Venue " + form.name.data + " was successfully listed!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash(
                "An error occurred. Venue " + form.name.data + " could not be listed."
            )

            return render_template("forms/new_venue.html", form=form)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(error)
                flash(
                    "Error in {}: {}".format(getattr(form, field).label.text, error),
                    "error",
                )

                return render_template("forms/new_venue.html", form=form)

    return render_template("pages/home.html")


@app.route("/venues/<int:venue_id>/delete", methods=["POST"])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)

        db.session.delete(venue)
        db.session.commit()
        print("Deleted")
        flash("Venue has been successfully deleted")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("An Error occurred. Venue could not be deleted.")
    finally:
        db.session.close()

    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    results = Artist.query.all()
    return render_template("pages/artists.html", artists=results)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "").strip()

    artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()

    list = []

    for artist in artists:
        shows = Show.query.filter(
            Show.venue_id == artist.id, Show.start_time >= datetime.now()
        ).all()

        list.append(
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": len(shows),
            }
        )

    response = {
        "count": len(artists),
        "data": list,
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    result = Artist.query.get(artist_id)

    shows = Show.query.filter(Show.artist_id == artist_id).all()

    past_shows = []
    upcoming_shows = []
    for s in shows:
        if s.start_time > datetime.now():
            upcoming_shows.append(
                {
                    "venue_image_link": s.venue.image_link,
                    "venue_id": s.venue_id,
                    "venue_name": s.venue.name,
                    "start_time": str(s.start_time),
                }
            )
        else:
            past_shows.append(
                {
                    "venue_image_link": s.venue.image_link,
                    "venue_id": s.venue_id,
                    "venue_name": s.venue.name,
                    "start_time": str(s.start_time),
                }
            )

    data = {
        "id": result.id,
        "name": result.name,
        "genres": ast.literal_eval(result.genres),
        "city": result.city,
        "state": result.state,
        "phone": result.phone,
        "image_link": result.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
        "seeking_venue": result.seeking_venue,
        "seeking_description": result.seeking_description,
        "facebook_link": result.facebook_link,
        "website": result.website_link,
    }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)

    form = ArtistForm(
        name=artist.name,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        image_link=artist.image_link,
        genres=ast.literal_eval(artist.genres),
        facebook_link=artist.facebook_link,
        website_link=artist.website_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
    )

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    try:
        artist = Artist.query.get(artist_id)

        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.image_link = form.image_link.data
        artist.genres = str(form.genres.data)
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.website_link = form.website_link.data

        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully Edited!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be Edited."
        )
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):

    venue = Venue.query.get(venue_id)

    form = VenueForm(
        name=venue.name,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        image_link=venue.image_link,
        genres=ast.literal_eval(venue.genres),
        facebook_link=venue.facebook_link,
        website_link=venue.website_link,
        seeking_description=venue.seeking_description,
        address=venue.address,
        seeking_talent=venue.seeking_talent,
    )

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    try:
        venue = Venue.query.get(venue_id)

        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.address = form.address.data
        venue.genres = str(form.genres.data)
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website_link = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.add(venue)
        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully Edited!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(
            "An error occurred. Venue " + request.form["name"] + " could not be Edited."
        )
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()

    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate_on_submit():
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=str(form.genres.data),
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_description=form.seeking_description.data,
            seeking_venue=form.seeking_venue.data,
        )

        try:
            db.session.add(artist)
            db.session.commit()
            flash("Artist " + request.form["name"] + " was successfully listed!")
        except:
            db.session.rollback()
            print(sys.exc_info())

            flash(
                "An error occurred. Artist " + form.name.data + " could not be listed."
            )

            return render_template("forms/new_artist.html", form=form)

    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(error)
                flash(
                    "Error in {}: {}".format(getattr(form, field).label.text, error),
                    "error",
                )

                return render_template("forms/new_artist.html", form=form)

    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    shows = Show.query.all()

    list = []

    for show in shows:

        list.append(
            {
                "venue_id": show.venue_id,
                "artist_id": show.artist_id,
                "venue_name": show.venue.name,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": str(show.start_time),
            }
        )

    return render_template("pages/shows.html", shows=list)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm(request.form)

    try:
        create_show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data,
        )
        db.session.add(create_show)
        db.session.commit()
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
# if __name__ == "__main__":
#     app.run(debug=True)

# Or specify port manually:
""""""
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
