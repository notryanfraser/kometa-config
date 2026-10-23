# kometa-config

Collection and poster files for [Kometa](https://kometa.wiki) (formerly Plex Meta Manager), running in Docker on Unraid with its config at `/mnt/user/appdata/plex_meta_manager`. `config.yml` holds API keys and tokens and is not kept here.

| File here | On the server | Library |
|---|---|---|
| `movie_collections.yml` | `Movie_collections.yml` | Movies collections |
| `movie_posters_tmdb.yml` | `Movie_posters_tmdb.yml` | Movies posters |
| `tv_collections.yml` | `TV_collections.yml` | TV Shows collections |
| `tv_posters.yml` | `TV_posters.yml` | TV Shows posters |

## Movie posters

`movie_posters_tmdb.yml` keys every movie by its TMDb id, with the title and year in a comment, sorted by that title:

```yaml
  16314: # 3 Ninjas (1992)
    url_poster: https://theposterdb.com/api/assets/18125/view
```

Every other movie in Plex has a commented-out placeholder in its place in the list. To give one a poster, replace `replaceMe` with the ThePosterDB asset id and remove the leading `# ` from both lines:

```yaml
  # 389: # 12 Angry Men (1957)
  #   url_poster: https://theposterdb.com/api/assets/replaceMe/view
```

Editions of the same movie share a TMDb id, so they use a key like `120 Extended` with a `match:` block on the id and edition.

## Placeholder true-up

`scripts/posters_trueup/` keeps the placeholders in step with Plex. It runs daily at 15:45, before Kometa's 16:00 run, as the Unraid User Script `kometa_posters_trueup` (`/boot/config/plugins/user.scripts/scripts/kometa_posters_trueup/`). `script` is the User Script; it runs `trueup.py` inside the Kometa container, which reads the Plex token from Kometa's own config.

Each run adds a placeholder for every Plex movie whose TMDb id is not in the file and removes placeholders for movies no longer in Plex. Entries with a poster are never changed. It writes only when something changed, keeps the last 7 dated backups, and changes nothing if Plex returns fewer than 1,000 movies; if it would remove more than 25 placeholders, it skips the removals.
