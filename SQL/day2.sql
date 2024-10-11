--Task 1: String Manipulations


--a: Concatenate Movie Title and Release Year, for example: The Wolf (2017).
SELECT 
    title || ' (' || release_year::INT || ')' AS movie_title_with_year
FROM 
    movies;

--b: Create a 'short title' column for the movie names containing only first 8 characters using Substring from Movies table.
SELECT 
    title,
    SUBSTRING(title, 1, 8) AS short_title
FROM 
    movies;


--c: Replace Spaces in actor names with underscores.
SELECT 
    name,
    REPLACE(name, ' ', '_') AS name_with_underscores
FROM 
    actors;

--d: Trim extra spaces in director names.
SELECT 
    name,
    TRIM(name) AS trimmed_name
FROM 
    directors;


--Task 2: Recent Movies and Actor Ages

--a: Select all movies released in the last 5 years and order them by box office revenue descending.
SELECT 
    title,
    release_year,
    box_office
FROM 
    movies
WHERE 
    release_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 5
ORDER BY 
    box_office DESC;


--b: Find age of all actors based on their birth year.
SELECT 
    name,
    birth_year,
    EXTRACT(YEAR FROM CURRENT_DATE) - birth_year AS age
FROM 
    actors;


--Task 3: Unions and Excepts
--a: Create a union of actors and directors names.
SELECT 
    name AS actor_dirctor
FROM 
    actors

UNION

SELECT 
    name AS actor_director
FROM 
    directors;

--b: Using EXCEPT operation find all unreviewed movies.
SELECT 
    movie_id,
    title
FROM 
    movies

EXCEPT

SELECT 
    m.movie_id,
    m.title
FROM 
    movies m
JOIN 
    ratings r ON m.movie_id = r.movie_id;


--Task 4: Intersection and Aggregation
--a: Find all movies directed by David Braun and Daniel Gonzales using INTERSECT.
SELECT 
    m.movie_id,
    m.title
FROM 
    movies m
JOIN 
    movie_directors md ON m.movie_id = md.movie_id
JOIN 
    directors d ON md.director_id = d.director_id
WHERE 
    d.name = 'David Braun'

INTERSECT

SELECT 
    m.movie_id,
    m.title
FROM 
    movies m
JOIN 
    movie_directors md ON m.movie_id = md.movie_id
JOIN 
    directors d ON md.director_id = d.director_id
WHERE 
    d.name = 'Daniel Gonzales';

--b: Find the actor with the most roles.
    SELECT 
    a.name,
    COUNT(ma.role) AS role_count
FROM 
    actors a
JOIN 
    movie_actors ma ON a.actor_id = ma.actor_id
GROUP BY 
  a.name
ORDER BY 
    role_count DESC
limit 1;


--c: Calculate the average age of directors at the time of their first movie release.
WITH FirstMovie AS (
    SELECT 
        md.director_id,
        MIN(m.release_year) AS first_movie_year
    FROM 
        movie_directors md
    JOIN 
        movies m ON md.movie_id = m.movie_id
    GROUP BY 
        md.director_id
),
DirectorAgeAtFirstMovie AS (
    SELECT 
        d.director_id,
        EXTRACT(YEAR FROM CURRENT_DATE) - d.birth_year AS current_age,
        f.first_movie_year,
        (f.first_movie_year - d.birth_year) AS age_at_first_movie
    FROM 
        FirstMovie f
    JOIN 
        directors d ON f.director_id = d.director_id
)
SELECT 
    AVG(age_at_first_movie) AS average_age_at_first_movie
FROM 
    DirectorAgeAtFirstMovie;



--Task 5: Genre and Budget Analysis
--a: Find the top 3 genres with the highest average budget for movies.
SELECT 
    g.name AS genre_name,
    AVG(m.budget) AS average_budget
FROM 
    movies m
JOIN 
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN 
    genres g ON mg.genre_id = g.genre_id
GROUP BY 
    g.name
ORDER BY 
    average_budget DESC
LIMIT 3;

--b: Find the top 3 genres with the lowest average budget for movies.
SELECT 
    g.name AS genre_name,
    AVG(m.budget) AS average_budget
FROM 
    movies m
JOIN 
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN 
    genres g ON mg.genre_id = g.genre_id
GROUP BY 
    g.name
ORDER BY 
    average_budget ASC
LIMIT 3;

--c: Calculate the average number of movies per genre *.
SELECT 
    g.name AS genre_name,
    COUNT(m.movie_id) AS movie_count,
    AVG(COUNT(m.movie_id)) OVER() AS average_movie_count
FROM
    movies m
JOIN
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN
    genres g ON mg.genre_id = g.genre_id
GROUP BY
    g.name
ORDER BY
    g.name;



--Task 6: Box Office and Ratings Analysis
--a: Find the year with the highest total box office revenue.
SELECT 
    release_year,
    SUM(box_office) AS total_box_office
FROM 
    movies
GROUP BY 
    release_year
ORDER BY 
    total_box_office desc
LIMIT 1;


--b: List all actors who have worked with a director named Carlos Griffith.
SELECT DISTINCT
    a.actor_id,
    a.name AS actor_name
FROM
    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id
JOIN
    movies m ON ma.movie_id = m.movie_id
JOIN
    movie_directors md ON m.movie_id = md.movie_id
JOIN
    directors d ON md.director_id = d.director_id
WHERE
    d.name = 'Carlos Griffith';


--c: Find the average rating of movies by director and genre.
SELECT 
    d.name AS director_name,
    g.name AS genre_name,
    AVG(r.rating) AS average_rating
FROM 
    movies m
JOIN 
    movie_directors md ON m.movie_id = md.movie_id
JOIN 
    directors d ON md.director_id = d.director_id
JOIN 
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN 
    genres g ON mg.genre_id = g.genre_id
JOIN 
    ratings r ON m.movie_id = r.movie_id
GROUP BY 
    d.name, g.name
ORDER BY 
    director_name, genre_name;


--Task 7: Counts and Averages
--a: Calculate the total number of movies, actors, and directors.
SELECT 
    'Movies' AS category,
    COUNT(movie_id) AS total_count
FROM 
    movies

UNION ALL

SELECT 
    'Actors' AS category,
    COUNT(actor_id) AS total_count
FROM 
    actors

UNION ALL

SELECT 
    'Directors' AS category,
    COUNT(director_id) AS total_count
FROM 
    directors;
--b: Find the actor who has worked in the most genres*.
SELECT 
    a.actor_id,
    a.name AS actor_name,
    COUNT(DISTINCT g.genre_id) AS genre_count
FROM
    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id
JOIN
    movies m ON ma.movie_id = m.movie_id
JOIN
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN
    genres g ON mg.genre_id = g.genre_id
GROUP BY
    a.actor_id, a.name
ORDER BY
    genre_count DESC
LIMIT 1;


--c: List all movies and their ratings, including movies without ratings, and indicate whether they have ratings or not.
SELECT
    m.movie_id,
    m.title AS movie_title,
    r.rating,
    CASE 
        WHEN r.rating IS NOT NULL THEN 'Has Rating'
        ELSE 'No Rating'
    END AS rating_status
FROM
    movies m
LEFT JOIN
    ratings r ON m.movie_id = r.movie_id
ORDER BY
    m.movie_id;

--Task 8: Directors and Genres
--a: Find the director who has the highest average rating for movies released in the last 10 years.
SELECT
    d.director_id,
    d.name AS director_name,
    AVG(r.rating) AS average_rating
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id
JOIN
    ratings r ON m.movie_id = r.movie_id
WHERE
    m.release_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 10
GROUP BY
    d.director_id, d.name
ORDER BY
    average_rating DESC
LIMIT 1;

--b: Calculate the average runtime of movies by genre and year.
SELECT
    g.name AS genre_name,
    m.release_year,
    AVG(m.runtime_minutes) AS average_runtime
FROM
    movies m
JOIN
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN
    genres g ON mg.genre_id = g.genre_id
GROUP BY
    g.name,
    m.release_year
ORDER BY
    g.name,
    m.release_year;



--c: Find the top 5 actors who have the highest average rating for their movies.
SELECT
    a.actor_id,
    a.name AS actor_name,
    AVG(r.rating) AS average_rating
FROM
    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id
JOIN
    movies m ON ma.movie_id = m.movie_id
JOIN
    ratings r ON m.movie_id = r.movie_id
GROUP BY
    a.actor_id, a.name
ORDER BY
    average_rating DESC
LIMIT 5;

--Task 9: Movie Statistics
--a: List all directors and the number of genres they have directed movies in.*
SELECT
    d.name AS director_name,
    COUNT(DISTINCT g.genre_id) AS genre_count
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id
JOIN
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN
    genres g ON mg.genre_id = g.genre_id
GROUP BY
    d.name
ORDER BY
    genre_count DESC;


--b: Find the movie with the highest number of positive reviews.
SELECT
   
    m.title AS movie_title,
    COUNT(r.rating) AS positive_review_count
FROM
    movies m
JOIN
    ratings r ON m.movie_id = r.movie_id
WHERE
    r.sentiment = 'positive'
GROUP BY
    m.title
ORDER BY
    positive_review_count DESC
LIMIT 1;

--c: Calculate the total box office revenue for each actor.
SELECT
    a.actor_id,
    a.name AS actor_name,
    SUM(m.box_office) AS total_box_office
FROM

    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id
JOIN
    movies m ON ma.movie_id = m.movie_id
GROUP BY
    a.actor_id, a.name
ORDER BY
    total_box_office DESC;

--Task 10: Reviews and Runtime
--a: List all movies that have received more than 50 reviews.
SELECT
    m.title AS movie_title,
    COUNT(r.rating) AS review_count
FROM
    movies m
JOIN
    ratings r ON m.movie_id = r.movie_id
GROUP BY
    m.title
HAVING
    COUNT(r.rating) > 50
ORDER BY
    review_count DESC;


--b: Find the top 3 genres with the most positive sentiment reviews.
SELECT
    g.name AS genre_name,
    COUNT(r.sentiment) AS positive_review_count
FROM
    genres g
JOIN
    movie_genres mg ON g.genre_id = mg.genre_id
JOIN
    movies m ON mg.movie_id = m.movie_id
JOIN
    ratings r ON m.movie_id = r.movie_id
WHERE
    r.sentiment = 'positive'
GROUP BY
    g.name
ORDER BY    
    positive_review_count DESC
LIMIT 3;


--c: Find the actor who has the longest average runtime in their movies.
SELECT
    a.actor_id,
    a.name AS actor_name,
    AVG(m.runtime_minutes) AS average_runtime
FROM
    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id
JOIN
    movies m ON ma.movie_id = m.movie_id
GROUP BY
    a.actor_id, a.name
ORDER BY
    average_runtime DESC
LIMIT 1;

--Task 11: Advanced Queries
--a: List all directors who have directed movies in the last 3 years.
SELECT
    d.name AS director_name
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id
WHERE
    m.release_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 3
GROUP BY
    d.name;

--b: Find the top 5 directors based on the total number of movies directed.
SELECT
    d.name AS director_name,
    COUNT( md.movie_id) AS movie_count
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
GROUP BY
    d.name
ORDER BY
    movie_count DESC
LIMIT 5;

--c: List the titles and box office revenue of movies with a runtime greater than the average runtime.
SELECT
    m.title AS movie_title,
    m.box_office
FROM
    movies m
WHERE
    m.runtime_minutes > (SELECT AVG(runtime_minutes) FROM movies);



--Task 12: Creating Views and Tables
--a: Create a view named academy_user_top_10_high_gross_movies_v for the top 10 highest-grossing movies.
CREATE VIEW filip_maric_top_10_high_gross_movies_v AS
SELECT
    title AS movie_title,
    box_office
FROM
    movies
ORDER BY
    box_office DESC
LIMIT 10;

--b: Create a table for storing summary statistics of movies named filip_maric_movie_statistics_t. Insert summary statistics into the movie_statistics table.
CREATE TABLE filip_maric_movie_statistics_t (
    genre VARCHAR(255),
    avg_budget NUMERIC(15, 2),
    avg_box_office NUMERIC(15, 2),
    total_movies INT
);

INSERT INTO filip_maric_movie_statistics_t (genre, avg_budget, avg_box_office, total_movies)
SELECT
    g.name AS genre,
    AVG(m.budget) AS avg_budget,
    AVG(m.box_office) AS avg_box_office,
    COUNT(m.movie_id) AS total_movies
FROM
    movies m
JOIN
    movie_genres mg ON m.movie_id = mg.movie_id
JOIN
    genres g ON mg.genre_id = g.genre_id
GROUP BY
    g.name;