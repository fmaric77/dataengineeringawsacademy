/* ask 1: ROW_NUMBER()
Objective: Select movie_id, title, release_year, and release_date from the movies table. Generate a unique sequence number for each group of movies that share the same release_year. Order primarily by release_year, and then by release_date.

HINT: Use PARTITION BY.*/
SELECT
    movie_id,
    title,
    release_year,
    release_date,
    ROW_NUMBER() OVER(PARTITION BY release_year ORDER BY release_date) AS sequence_number
FROM
    movies;


/*Task 2: Check the Results
Objective: Check the results, especially paying attention to the release_date. Notice that the date format is not consistent. Modify the query to change release_date to the proper date format (DD-MM-YYYY).*/
SELECT
    movie_id,
    title,
    release_year,
    TO_CHAR(
        CASE
            WHEN release_date LIKE '%/%/%' THEN TO_DATE(release_date, 'DD/MM/YYYY')
            WHEN release_date LIKE '%-%-%' THEN TO_DATE(release_date, 'YYYY-MM-DD')
        END,
        'DD-MM-YYYY'
    ) AS release_date,
    ROW_NUMBER() OVER(PARTITION BY release_year ORDER BY release_date) AS sequence_number
FROM
    movies;


/*Task 3: List Roles per Actor
Objective: List all roles per actor with a row number.*/
SELECT
    a.name AS actor_name,
    ma.role,
    ROW_NUMBER() OVER(PARTITION BY a.name ORDER BY ma.role) AS sequence_number
FROM
    actors a
JOIN
    movie_actors ma ON a.actor_id = ma.actor_id;


/*Task 4: Average Age with RANK()
Objective: Find the average age from the actors table based on nationality using RANK(). Note: first, calculate the average age. */
WITH actor_ages AS (
    SELECT
        actor_id,
        name,
        nationality,
        EXTRACT(YEAR FROM CURRENT_DATE) - birth_year AS age
    FROM
        actors
),
ranked_actors AS (
    SELECT
        actor_id,
        name,
        nationality,
        age,
        RANK() OVER (PARTITION BY nationality ORDER BY age DESC) AS age_rank
    FROM
        actor_ages
)
SELECT
    nationality,
    AVG(age) AS average_age
FROM
    ranked_actors
GROUP BY
    nationality
ORDER BY
    average_age DESC;



/*Task 5: Rank Actors by Number of Roles
Objective: Rank actors based on the number of roles. Use the RANK() window function.*/
WITH actor_roles AS (
    SELECT
        a.name AS actor_name,
        COUNT(ma.role) AS number_of_roles
    FROM
        actors a
    JOIN
        movie_actors ma ON a.actor_id = ma.actor_id
    GROUP BY
        a.name
)
SELECT
    actor_name,
    number_of_roles,
    RANK() OVER (ORDER BY number_of_roles DESC) AS role_rank
FROM
    actor_roles
ORDER BY
    role_rank;


/*Task 6: Count Roles per Actor with DENSE_RANK()
Objective: Count roles per actor and rank using DENSE_RANK(). Check the difference with the previous results.*/
WITH actor_roles AS (
    SELECT
        a.name AS actor_name,
        COUNT(ma.role) AS number_of_roles
    FROM
        actors a
    JOIN
        movie_actors ma ON a.actor_id = ma.actor_id
    GROUP BY
        a.name
)
SELECT
    actor_name,
    number_of_roles,
    DENSE_RANK() OVER (ORDER BY number_of_roles DESC) AS role_rank
FROM
    actor_roles
ORDER BY
    role_rank;


/*Task 7: Categorize Movies with NTILE()
Objective: Use the NTILE() function to categorize movies into 5 groups based on their average ratings. Only categorize movies that were released in 2020. Return the following columns: movie_id, title, release_year, average_rating, rating_category.*/
WITH movie_ratings AS (
    SELECT
        m.movie_id,
        m.title,
        m.release_year,
        AVG(r.rating) AS average_rating
    FROM
        movies m
    JOIN
        ratings r ON m.movie_id = r.movie_id
    WHERE
        m.release_year = 2020
    GROUP BY
        m.movie_id,
        m.title,
        m.release_year
)
SELECT
    movie_id,
    title,
    release_year,
    average_rating,
    NTILE(5) OVER (ORDER BY average_rating) AS rating_category
FROM
    movie_ratings
ORDER BY
    average_rating DESC;


/*Task 8: LEAD() and LAG()*/
--a: Select movies released in 1985. Retrieve the following columns: title, runtime_minutes, budget, and release_year of each movie.
SELECT
    title,
    runtime_minutes,
    budget,
    release_year
FROM
    movies
WHERE
    release_year = 1985;
--b: Add a column that will get the title of the next movie in the budget order using the LEAD() function.
SELECT
    title,
    runtime_minutes,
    budget,
    release_year,
    LEAD(title) OVER (ORDER BY budget) AS next_movie
FROM
    movies
WHERE
    release_year = 1985;

--c: Add a column that will get the title of the previous movie in the budget order using the LAG() function*.
SELECT
    title,
    runtime_minutes,
    budget,
    release_year,
    LEAD(title) OVER (ORDER BY budget) AS next_movie,
    LAG(title) OVER (ORDER BY budget) AS previous_movie
FROM
    movies
WHERE
    release_year = 1985;

--d: Order the results by budget.
SELECT
    title,
    runtime_minutes,
    budget,
    release_year,
    LEAD(title) OVER (ORDER BY budget) AS next_movie,
    LAG(title) OVER (ORDER BY budget) AS previous_movie
FROM
    movies
WHERE
    release_year = 1985
ORDER BY
    budget;


--e: Modify the window functions to return the titles of the next two, and previous four movies in the budget order. Check the results.
SELECT
    title,
    runtime_minutes,
    budget,
    release_year,
    LEAD(title, 1) OVER (ORDER BY budget) AS next_movie_1,
    LEAD(title, 2) OVER (ORDER BY budget) AS next_movie_2,
    LAG(title, 1) OVER (ORDER BY budget) AS previous_movie_1,
    LAG(title, 2) OVER (ORDER BY budget) AS previous_movie_2,
    LAG(title, 3) OVER (ORDER BY budget) AS previous_movie_3,
    LAG(title, 4) OVER (ORDER BY budget) AS previous_movie_4
FROM
    movies
WHERE
    release_year = 1985
ORDER BY
    budget;

--Task 9: FIRST_VALUE() and LAST_VALUE()
--a: List each director (id, name) along with their movies and the movie budgets. For each director, generate a unique row number for each movie ordered by the movie title using ROW_NUMBER().
SELECT
    d.director_id,
    d.name AS director_name,
    m.title,
    m.budget,
    ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS sequence_number
FROM
    directors d
join movie_directors on movie_directors.director_id = d.director_id

JOIN
    movies m ON movie_directors.movie_id = m.movie_id;

--b: For each director, calculate the first and last movie budgets in the ordered list of their movies. Use FIRST_VALUE() and LAST_VALUE() to find the budget of the first/last movie in the list for each director.
SELECT
    d.director_id,
    d.name AS director_name,
    m.title,
    m.budget,
    ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS sequence_number,
    FIRST_VALUE(m.budget) OVER (PARTITION BY d.director_id ORDER BY m.title ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS first_movie_budget,
    LAST_VALUE(m.budget) OVER (PARTITION BY d.director_id ORDER BY m.title ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_movie_budget
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id;
    

--c: Validate the query by checking if the window functions provide the correct results for a few sample directors. Add a WHERE clause of your choice.
SELECT
    d.director_id,
    d.name AS director_name,
    m.title,
    m.budget,
    ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS sequence_number,
    FIRST_VALUE(m.budget) OVER (PARTITION BY d.director_id ORDER BY m.title ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS first_movie_budget,
    LAST_VALUE(m.budget) OVER (PARTITION BY d.director_id ORDER BY m.title ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_movie_budget
FROM
    directors d
JOIN
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id
WHERE
    d.director_id IN (SELECT director_id FROM directors ORDER BY RANDOM() LIMIT 3)
ORDER BY
    director_name,
    sequence_number;


/*Task 10: Debugging a Query
Objective: Identify what is wrong with the following query. Rewrite it and find two ways to correct it.

HINT: Use HAVING and COUNT window function.*/


--Original Query
SELECT
 md.director_id,
 COUNT(md.movie_id) AS cnt_movies
FROM public.movie_directors md
WHERE cnt_movies > 10
GROUP BY md.director_id
ORDER BY cnt_movies;


--corrected query
SELECT
    md.director_id,
    COUNT(md.movie_id) AS cnt_movies
FROM 
    public.movie_directors md
GROUP BY 
    md.director_id
HAVING 
    COUNT(md.movie_id) > 10
ORDER BY 
    cnt_movies;


--a: Write a query that will list each director along with the movie unique identifier for each movie they have directed, using the ROW_NUMBER() function. The result should return all columns from the directors table and a new column cnt_movies which shows a sequential number for each movie directed by a director.
SELECT
    d.director_id,
    d.name AS director_name,
    m.title,
    m.budget,
    ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS cnt_movies
FROM
    directors d
JOIN    
    movie_directors md ON d.director_id = md.director_id
JOIN
    movies m ON md.movie_id = m.movie_id;



    

--b: Rewrite the previous query using the WITH clause.
WITH director_movies AS (
    SELECT
        d.director_id,
        d.name AS director_name,
        m.title,
        m.budget,
        ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS cnt_movies
    FROM
        directors d
    JOIN
        movie_directors md ON d.director_id = md.director_id
    JOIN
        movies m ON md.movie_id = m.movie_id
)
SELECT
    director_id,
    director_name,
    title,
    budget,
    cnt_movies
FROM
    director_movies;




--c: Calculate the maximum and minimum count of movies per director in the ranked_movies CTE. Note: also use WITH clause.
WITH director_movies AS (
    SELECT
        d.director_id,
        d.name AS director_name,
        m.title,
        m.budget,
        ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS cnt_movies
    FROM
        directors d
    JOIN
        movie_directors md ON d.director_id = md.director_id
    JOIN
        movies m ON md.movie_id = m.movie_id
),
minmax AS (
    SELECT
        MAX(cnt_movies) AS max_cnt,
        MIN(cnt_movies) AS min_cnt
    FROM
        director_movies
)
SELECT
    director_id,
    director_name,
    title,
    budget,
    cnt_movies,
    max_cnt,
    min_cnt
FROM
    director_movies, minmax;




--d: Use the NTILE(4) function to divide directors into four categories based on their movie counts.
WITH director_movies AS (
    SELECT
        d.director_id,
        d.name AS director_name,
        m.title,
        m.budget,
        ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.title) AS cnt_movies
    FROM
        directors d
    JOIN
        movie_directors md ON d.director_id = md.director_id
    JOIN
        movies m ON md.movie_id = m.movie_id
),
minmax AS (
    SELECT
        MAX(cnt_movies) AS max_cnt,
        MIN(cnt_movies) AS min_cnt
    FROM
        director_movies
)
SELECT
    director_id,
    director_name,
    title,
    budget,
    cnt_movies,
    max_cnt,
    min_cnt,
    NTILE(4) OVER (ORDER BY cnt_movies) AS mv_cnt_cat
FROM
    director_movies, minmax
ORDER BY
    cnt_movies DESC;




--e: The final result should have the following columns: director_id, director_name, max_cnt, min_cnt, and mv_cnt_cat. Order it by max_cnt from the largest to smallest.
WITH director_movies AS (
    SELECT
        d.director_id,
        d.name AS director_name,
        m.movie_id,
        ROW_NUMBER() OVER (PARTITION BY d.director_id ORDER BY m.movie_id) AS cnt_movies
    FROM
        directors d
    JOIN
        movie_directors md ON d.director_id = md.director_id
    JOIN
        movies m ON md.movie_id = m.movie_id
),
ranked_movies AS (
    SELECT
        director_id,
        director_name,
        movie_id,
        cnt_movies,
        MAX(cnt_movies) OVER (PARTITION BY director_id) AS max_movies,
        MIN(cnt_movies) OVER (PARTITION BY director_id) AS min_movies,
        COUNT(movie_id) OVER (PARTITION BY director_id) AS total_movies
    FROM
        director_movies
)
SELECT
    director_id,
    director_name,
    max_movies AS max_cnt,
    min_movies AS min_cnt,
    NTILE(4) OVER (PARTITION BY director_id ORDER BY cnt_movies) AS mv_cnt_cat
FROM
    ranked_movies

ORDER BY
    max_cnt DESC;