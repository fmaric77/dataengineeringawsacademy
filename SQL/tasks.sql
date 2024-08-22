select * from movies 
LIMIT 5;

select * from genres 
LIMIT 5;

select * from directors 
LIMIT 5;

select * from movies 
where release_year > 2000;

select * from directors 
where birth_year < 1970;

select * from movies 
where runtime_minutes > 150;

SELECT * from movies where release_year = 2010
order by budget desc;

SELECT * from movies 
order by box_office desc
LIMIT 5;

SELECT * from movies 
where budget BETWEEN 10000000 and 50000000


SELECT movies.title, movies.release_year 
FROM movies
JOIN movie_directors ON movies.movie_id = movie_directors.movie_id
JOIN directors on movie_directors.director_id = directors.director_id
WHERE directors.name LIKE 'Steven Spielberg'; /*Nema ga u tablici*/



SELECT
    movies.title
FROM
    movies
JOIN movie_genres ON movies.movie_id = movie_genres.movie_id
JOIN genres ON genres.genre_id = movie_genres.genre_id
WHERE genres.name LIKE 'Action';


SELECT
    movies.title, directors.name
FROM
    movies
JOIN movie_directors ON movies.movie_id = movie_directors.movie_id
JOIN directors ON directors.director_id = movie_directors.director_id
WHERE movies.release_year = 2020;


SELECT
    movies.title,
    genres.name AS genre_name
FROM
    movies
JOIN
    movie_genres ON movies.movie_id = movie_genres.movie_id
JOIN
    genres ON movie_genres.genre_id = genres.genre_id
ORDER BY
    movies.title,
    genres.name;


SELECT
    movies.title,
    actors.name AS actor_name
FROM
    movies
JOIN
    movie_actors ON movies.movie_id = movie_actors.movie_id
JOIN
    actors ON movie_actors.actor_id = actors.actor_id

ORDER BY
    movies.title,
    actors.name;



SELECT
    DISTINCT movies.movie_id,
    movies.title,
    movies.release_year,
    directors.director_id,
    directors.name AS director_name,
    actors.actor_id,
    actors.name AS actor_name
FROM
    movies
JOIN
    movie_directors ON movies.movie_id = movie_directors.movie_id
JOIN
    directors ON movie_directors.director_id = directors.director_id
JOIN
    movie_actors ON movies.movie_id = movie_actors.movie_id
JOIN
    actors ON movie_actors.actor_id = actors.actor_id
WHERE
    directors.director_id = actors.actor_id
ORDER BY
    movies.title,
    directors.name;





SELECT
    senior_directors.director_id AS senior_director_id,
    senior_directors.name AS senior_director_name,
    assistant_directors.assistant_director_id,
    assistant_directors_details.name AS assistant_director_name
FROM
    assistant_directors
JOIN
    directors AS senior_directors
ON
    assistant_directors.senior_director_id = senior_directors.director_id
JOIN
    directors AS assistant_directors_details
ON
    assistant_directors.assistant_director_id = assistant_directors_details.director_id
ORDER BY
    senior_directors.director_id,
    assistant_directors.assistant_director_id;



SELECT
    directors.director_id,
    directors.name,
    assistant_directors.assistant_director_id,
    assistant_directors_details.name
FROM
    assistant_directors
JOIN
    directors
ON
    assistant_directors.senior_director_id = directors.director_id
JOIN
    directors AS assistant_directors_details
ON
    assistant_directors.assistant_director_id = assistant_directors_details.director_id
ORDER BY
    directors.director_id,
    assistant_directors.assistant_director_id;



SELECT
    movies.movie_id,
    movies.title,
    movies.release_year,
    directors.director_id,
    directors.name,
    genres.genre_id,
    genres.name
FROM
    movies
JOIN
    movie_directors ON movies.movie_id = movie_directors.movie_id
JOIN
    directors ON movie_directors.director_id = directors.director_id
JOIN
    movie_genres ON movies.movie_id = movie_genres.movie_id
JOIN
    genres ON movie_genres.genre_id = genres.genre_id
ORDER BY
    movies.movie_id,
    directors.director_id,
    genres.genre_id;



SELECT
    actors.name AS actor_name,
    movies.title AS movie_title
FROM
    movie_directors
JOIN
    directors ON movie_directors.director_id = directors.director_id
JOIN
    movies ON movie_directors.movie_id = movies.movie_id
JOIN
    movie_actors ON movies.movie_id = movie_actors.movie_id
JOIN
    actors ON movie_actors.actor_id = actors.actor_id
WHERE
    directors.name = 'Bryan Hill'
ORDER BY
    actors.actor_id,
    movies.title;





SELECT
    genres.name AS genre_name,
    directors.name AS director_name
FROM
    genres
CROSS JOIN directors


/*Nema ga*/
SELECT 
    ad1.assistant_director_id,
    ad2.name,
    ad2.nationality,
    ad3.name,
    ad3.nationality
FROM 
    assistant_directors AS ad1
JOIN 
    directors AS ad2 ON ad1.senior_director_id = ad2.director_id
JOIN 
    directors AS ad3 ON ad1.assistant_director_id = ad3.director_id
WHERE 
    ad2.nationality = ad3.nationality;




SELECT 
    m.title AS movie_title,
    d.name AS director_name,
    ad_s.name AS assistant_director_name
FROM 
    movies m
JOIN 
    movie_directors md ON m.movie_id = md.movie_id
JOIN 
    directors d ON md.director_id = d.director_id
INNER JOIN 
    assistant_directors ad ON d.director_id = ad.senior_director_id
INNER JOIN 
    directors ad_s ON ad.assistant_director_id = ad_s.director_id
ORDER BY 
    m.title, d.name, ad_s.name;


    select distinct movies.title from movies 
join movie_directors on movies.movie_id = movie_directors.movie_id
join directors on directors.director_id = movie_directors.movie_id
where directors.nationality like 'United States of America';


select DISTINCT movies.title, actors.name from movies 
join movie_directors on movies.movie_id = movie_directors.movie_id
join directors on directors.director_id = movie_directors.movie_id
join movie_actors on movie_actors.movie_id = movies.movie_id
join actors on actors.actor_id = movie_actors.actor_id
where directors.nationality = actors.nationality;


  select  distinct movies.title from movies 
join movie_directors on movies.movie_id = movie_directors.movie_id
join directors on directors.director_id = movie_directors.movie_id
where directors.nationality like 'United Kingdom';


SELECT movies.title, genres.name as genre_name,  directors.name as director_name
from movies 
join movie_directors on movie_directors.movie_id = movies.movie_id
join directors on movie_directors.director_id = directors.director_id
join movie_genres on movie_genres.movie_id = movies.movie_id
join genres on genres.genre_id= movie_genres.genre_id
order by box_office desc;


SELECT distinct actors.name
from movies 
join movie_directors on movie_directors.movie_id = movies.movie_id
join directors on movie_directors.director_id = directors.director_id
join movie_actors on movies.movie_id = movie_actors.movie_id
join actors on actors.actor_id= movie_actors.actor_id
where directors.birth_year >1960 and actors.birth_year>1960;


SELECT 
    m.title AS movie_title,
    d.name AS director_name,
    d.nationality AS director_nationality,
    ad_s.name AS assistant_director_name,
    ad_s.nationality AS assistant_director_nationality
FROM 
    movies m
JOIN 
    movie_directors md ON m.movie_id = md.movie_id
JOIN 
    directors d ON md.director_id = d.director_id
INNER JOIN 
    assistant_directors ad ON d.director_id = ad.senior_director_id
INNER JOIN 
    directors ad_s ON ad.assistant_director_id = ad_s.director_id
WHERE 
    d.nationality <> ad_s.nationality
ORDER BY 
    m.title, d.name, ad_s.name;



