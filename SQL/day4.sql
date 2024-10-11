/*
### Task 1: Create a Stored Procedure to Update Date Format

- **Objective**: Create a stored procedure that will update the `release_date` column to the proper date format (DD-MM-YYYY). The stored procedure should take two input parameters (table name and column name you want to format).

  - **a**: Before running the procedure, copy data from the `movies` table into a new table and add a suffix with your surname at the end of the table name.
  - **b**: Run the procedure on the new table and compare results.
  - **c**: Did the date get corrected? Is there something wrong? And why? You can shortly describe in your own words.


*/

CREATE TABLE movies_maric AS 
SELECT * 
FROM movies;

CREATE OR REPLACE PROCEDURE Update_date_maric(tbl VARCHAR(50), col VARCHAR(50))
AS $$
BEGIN
  EXECUTE 'UPDATE ' || tbl || ' SET ' || col || ' = TO_DATE(TO_CHAR(
        CASE
            WHEN release_date LIKE ''%-%-%'' THEN TO_DATE(release_date, ''YYYY-MM-DD'')
            WHEN release_date LIKE ''%/%/%'' THEN TO_DATE(release_date, ''DD/MM/YYYY'')
        END,
        ''DD-MM-YYYY''
    ), ''DD-MM-YYYY'')';
END;
$$
LANGUAGE plpgsql;
 
 
CALL Update_date_maric('movies_maric', 'release_date');




--### Task 2: Create a Dimension Table and Stored Procedure

-- **a**: Create a new table `dim_movies` and add your surname as a suffix to the table name. The table should have the following columns: `movie title`, `release_year`, `runtime_minutes`, `director_id`, `director name`, `director nationality`, `actor_id`, `actor name`, `actor nationality`.
CREATE TABLE dim_movies_maric (
    movie_title VARCHAR(255),
    release_year INTEGER,
    runtime_minutes INTEGER,
    director_id INTEGER,
    director_name VARCHAR(255),
    director_nationality VARCHAR(255),
    actor_id INTEGER,
    actor_name VARCHAR(255),
    actor_nationality VARCHAR(255)
);

  
-- **b**: Create a stored procedure that will load data into this new table. Ensure that when executing the procedure, data will first be deleted, and only new data will be inserted into the table. Also, you should load data from the last two years.
CREATE OR REPLACE PROCEDURE load_dim_movies_maric()
AS $$
BEGIN
    DELETE FROM dim_movies_maric;

    INSERT INTO dim_movies_maric (movie_title, release_year, runtime_minutes, director_id, director_name, director_nationality, actor_id, actor_name, actor_nationality)
    SELECT 
        m.title AS movie_title,
        m.release_year,
        m.runtime_minutes,
        d.director_id,
        d.name AS director_name,
        d.nationality AS director_nationality,
        a.actor_id,
        a.name AS actor_name,
        a.nationality AS actor_nationality
    FROM movies m
    JOIN movie_directors md ON m.movie_id = md.movie_id
    JOIN directors d ON md.director_id = d.director_id
    JOIN movie_actors ma ON m.movie_id = ma.movie_id
    JOIN actors a ON ma.actor_id = a.actor_id
    WHERE m.release_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 2;
END;
$$ LANGUAGE plpgsql;

CALL load_dim_movies_maric();


--### Task 3: Find Movies with the Highest Average Rating

-- **Objective**: Find the movies with the highest average rating. Return the movie titles and average rating.
CREATE OR REPLACE PROCEDURE highest_rated_movies_maric()
AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT m.title, AVG(r.rating) AS avg_rating
        FROM movies m
        JOIN ratings r ON m.movie_id = r.movie_id
        GROUP BY m.title
        ORDER BY avg_rating DESC
    LOOP
        RAISE NOTICE '% %', rec.title, rec.avg_rating;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

--CALL highest_rated_movies_maric();

--Without the procedure*
SELECT m.title, AVG(r.rating) AS avg_rating
FROM movies m
JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY m.title
ORDER BY avg_rating DESC;


--### Task 4: Find Movie Titles with Frequent Actors

--- **Objective**: Find movie titles that feature actors who have acted in more than five movies. Order by title.
CREATE OR REPLACE PROCEDURE frequent_actors_maric()
AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT m.title
        FROM movies m
        JOIN movie_actors ma ON m.movie_id = ma.movie_id
        JOIN actors a ON ma.actor_id = a.actor_id
        GROUP BY m.title
        HAVING COUNT(a.actor_id) > 5
        ORDER BY m.title
    LOOP
        RAISE NOTICE '%', rec.title;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CALL frequent_actors_maric();


--Without the procedure*
SELECT m.title
FROM movies m
JOIN movie_actors ma ON m.movie_id = ma.movie_id
JOIN actors a ON ma.actor_id = a.actor_id
GROUP BY m.title
HAVING COUNT(a.actor_id) > 5
ORDER BY m.title;

--### Task 5: Find Pairs of Directors with the Same Last Name

-- **Objective**: Write a query to find pairs of directors who share the same last name. The output should include the names of both directors.


WITH SplitNames AS (
    SELECT 
        name, 
        TRIM(
            SPLIT_PART(
                TRIM(
                    REGEXP_REPLACE(
                        name,
                        '(Mr.|Mrs.|Ms.|Dr.|DVM|Jr.|PhD|MD|DDS|Miss|JS|IV|II)\s*',
                        ''
                    )
                ), 
                ' ', 
                2
            )
        ) AS last_name
    FROM directors
),
DirectorPairs AS (
    SELECT
        d1.name AS director1,
        d2.name AS director2
    FROM SplitNames d1
    JOIN SplitNames d2 ON d1.last_name = d2.last_name AND d1.name < d2.name
)
SELECT director1, director2
FROM DirectorPairs
ORDER BY director1, director2;

--### Task 6: Find Pairs of Assistant Directors Reporting to the Same Director

-- **Objective**: Write a query to list pairs of assistant directors who report to the same director. The output should include the names of both assistants and their director.
-- No procedure
SELECT
    ad1.assistant_director_id AS assistant1_id,
    ad2.assistant_director_id AS assistant2_id,
    d1.name AS assistant1_name,
    d2.name AS assistant2_name,
    d3.name AS director_name
FROM
    assistant_directors ad1
JOIN
    assistant_directors ad2
    ON ad1.senior_director_id = ad2.senior_director_id
    AND ad1.assistant_director_id < ad2.assistant_director_id
JOIN
    directors d1
    ON ad1.assistant_director_id = d1.director_id
JOIN
    directors d2
    ON ad2.assistant_director_id = d2.director_id
JOIN
    directors d3
    ON ad1.senior_director_id = d3.director_id
ORDER BY
    director_name, assistant1_name, assistant2_name;


--with procedure
CREATE OR REPLACE PROCEDURE same_director_assistants_maric()
AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT
            ad1.assistant_director_id AS assistant1_id,
            ad2.assistant_director_id AS assistant2_id,
            d1.name AS assistant1_name,
            d2.name AS assistant2_name,
            d3.name AS director_name
        FROM
            assistant_directors ad1
        JOIN
            assistant_directors ad2
            ON ad1.senior_director_id = ad2.senior_director_id
            AND ad1.assistant_director_id < ad2.assistant_director_id
        JOIN
            directors d1
            ON ad1.assistant_director_id = d1.director_id
        JOIN
            directors d2
            ON ad2.assistant_director_id = d2.director_id
        JOIN
            directors d3
            ON ad1.senior_director_id = d3.director_id
        ORDER BY
            director_name, assistant1_name, assistant2_name
    LOOP
        RAISE NOTICE '% | % | % | % | %', rec.assistant1_id, rec.assistant2_id, rec.assistant1_name, rec.assistant2_name, rec.director_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;


--CALL same_director_assistants_maric();