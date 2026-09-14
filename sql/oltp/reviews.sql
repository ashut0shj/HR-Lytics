-- insert a performance review
INSERT INTO reviews
    (employee_id, review_date, performance_rating, job_satisfaction,
     environment_satisfaction, relationship_satisfaction, work_life_balance)
VALUES
    (%(emp_id)s, %(rdate)s, %(perf)s, %(job_sat)s, %(env_sat)s, %(rel_sat)s, %(wlb)s);

-- get all reviews for an employee
SELECT * FROM reviews WHERE employee_id = %(id)s ORDER BY review_date DESC;

