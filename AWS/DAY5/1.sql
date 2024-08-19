--1

CREATE TABLE ratings_overview AS
SELECT 
    CASE 
        WHEN CAST(averagerating AS DOUBLE) >= 0 AND CAST(averagerating AS DOUBLE) < 1 THEN '0-1'
        WHEN CAST(averagerating AS DOUBLE) >= 1 AND CAST(averagerating AS DOUBLE) < 2 THEN '1-2'
        WHEN CAST(averagerating AS DOUBLE) >= 2 AND CAST(averagerating AS DOUBLE) < 3 THEN '2-3'
        WHEN CAST(averagerating AS DOUBLE) >= 3 AND CAST(averagerating AS DOUBLE) < 4 THEN '3-4'
        WHEN CAST(averagerating AS DOUBLE) >= 4 AND CAST(averagerating AS DOUBLE) < 5 THEN '4-5'
        WHEN CAST(averagerating AS DOUBLE) >= 5 AND CAST(averagerating AS DOUBLE) < 6 THEN '5-6'
        WHEN CAST(averagerating AS DOUBLE) >= 6 AND CAST(averagerating AS DOUBLE) < 7 THEN '6-7'
        WHEN CAST(averagerating AS DOUBLE) >= 7 AND CAST(averagerating AS DOUBLE) < 8 THEN '7-8'
        WHEN CAST(averagerating AS DOUBLE) >= 8 AND CAST(averagerating AS DOUBLE) < 9 THEN '8-9'
        WHEN CAST(averagerating AS DOUBLE) >= 9 AND CAST(averagerating AS DOUBLE) <= 10 THEN '9-10'
    END AS rating_range,
    COUNT(tconst) AS title_count,
    SUM(CAST(numvotes AS BIGINT)) AS total_votes
FROM 
title_ratings
GROUP BY 
    CASE 
        WHEN CAST(averagerating AS DOUBLE) >= 0 AND CAST(averagerating AS DOUBLE) < 1 THEN '0-1'
        WHEN CAST(averagerating AS DOUBLE) >= 1 AND CAST(averagerating AS DOUBLE) < 2 THEN '1-2'
        WHEN CAST(averagerating AS DOUBLE) >= 2 AND CAST(averagerating AS DOUBLE) < 3 THEN '2-3'
        WHEN CAST(averagerating AS DOUBLE) >= 3 AND CAST(averagerating AS DOUBLE) < 4 THEN '3-4'
        WHEN CAST(averagerating AS DOUBLE) >= 4 AND CAST(averagerating AS DOUBLE) < 5 THEN '4-5'
        WHEN CAST(averagerating AS DOUBLE) >= 5 AND CAST(averagerating AS DOUBLE) < 6 THEN '5-6'
        WHEN CAST(averagerating AS DOUBLE) >= 6 AND CAST(averagerating AS DOUBLE) < 7 THEN '6-7'
        WHEN CAST(averagerating AS DOUBLE) >= 7 AND CAST(averagerating AS DOUBLE) < 8 THEN '7-8'
        WHEN CAST(averagerating AS DOUBLE) >= 8 AND CAST(averagerating AS DOUBLE) < 9 THEN '8-9'
        WHEN CAST(averagerating AS DOUBLE) >= 9 AND CAST(averagerating AS DOUBLE) <= 10 THEN '9-10'
    END
ORDER BY 
    rating_range;


--2
CREATE TABLE title_insights AS
SELECT 
    titletype,
    MIN(CAST(startyear AS INT)) AS min_startyear,
    MAX(CAST(startyear AS INT)) AS max_startyear,
    MAX(CAST(startyear AS INT)) - MIN(CAST(startyear AS INT)) AS year_difference
FROM 
    title_basics
WHERE 
    primarytitle = originaltitle 
    AND titletype IN (
        SELECT DISTINCT titletype 
        FROM title_basics
        LIMIT 4
    )
    AND startyear != '\N'  
GROUP BY 
    titletype;



-- titletype             min_startyear  max_startyear  year_difference
-- --------------------------------------------------------
-- 1          tvEpisode      1949           2022            73
-- 2          short          1892           2023            131
-- 3          movie          1894           2023            129
-- 4          tvMovie        1939           2019            80



--redshift
Elapsed time: 12407 ms


--athena
Time in queue:
60 ms
Run time:
1.282 sec
Data scanned:
7.62 MB


--Athena executes the query faster than Redshift. The query is simple and does not require a lot of resources. Athena is serverless and can scale automatically to handle the query. Redshift is a managed data warehouse and requires more resources to execute the query.