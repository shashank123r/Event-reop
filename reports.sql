-- Campus Event Reporting System - SQL Reports
-- Execute these queries directly in your SQLite database or through the API endpoints

-- ===============================================
-- 1. TOTAL REGISTRATIONS PER EVENT
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_date,
    c.name AS college_name,
    COUNT(r.id) AS total_registrations,
    SUM(CASE WHEN r.status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed_registrations,
    SUM(CASE WHEN r.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_registrations,
    e.max_capacity - SUM(CASE WHEN r.status = 'confirmed' THEN 1 ELSE 0 END) AS available_spots
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_date, c.name, e.max_capacity
ORDER BY total_registrations DESC;

-- ===============================================
-- 2. ATTENDANCE PERCENTAGE PER EVENT
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_date,
    c.name AS college_name,
    COUNT(DISTINCT r.id) AS total_registered,
    COUNT(DISTINCT a.id) AS total_attended,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT r.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT r.id))
        END, 2
    ) AS attendance_percentage
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON e.id = a.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_date, c.name
HAVING total_registered > 0
ORDER BY attendance_percentage DESC;

-- ===============================================
-- 3. AVERAGE FEEDBACK SCORE PER EVENT
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_date,
    c.name AS college_name,
    COUNT(f.id) AS total_feedback,
    ROUND(AVG(f.rating), 2) AS average_rating,
    SUM(CASE WHEN f.rating = 5 THEN 1 ELSE 0 END) AS five_star,
    SUM(CASE WHEN f.rating = 4 THEN 1 ELSE 0 END) AS four_star,
    SUM(CASE WHEN f.rating = 3 THEN 1 ELSE 0 END) AS three_star,
    SUM(CASE WHEN f.rating = 2 THEN 1 ELSE 0 END) AS two_star,
    SUM(CASE WHEN f.rating = 1 THEN 1 ELSE 0 END) AS one_star
FROM events e
LEFT JOIN feedback f ON e.id = f.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_date, c.name
HAVING total_feedback > 0
ORDER BY average_rating DESC, total_feedback DESC;

-- ===============================================
-- 4. EVENT POPULARITY REPORT (SORTED BY REGISTRATIONS)
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_type,
    e.event_date,
    c.name AS college_name,
    COUNT(DISTINCT r.id) AS registrations,
    COUNT(DISTINCT a.id) AS attendance,
    ROUND(AVG(f.rating), 2) AS avg_rating,
    -- Popularity Score: 40% registrations + 40% attendance + 20% rating
    ROUND(
        (COUNT(DISTINCT r.id) * 0.4) + 
        (COUNT(DISTINCT a.id) * 0.4) + 
        (COALESCE(AVG(f.rating), 0) * 4 * 0.2), 2
    ) AS popularity_score
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON e.id = a.event_id
LEFT JOIN feedback f ON e.id = f.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_type, e.event_date, c.name
ORDER BY popularity_score DESC, registrations DESC
LIMIT 20;

-- ===============================================
-- 5. STUDENT PARTICIPATION REPORT
-- ===============================================
SELECT 
    s.id AS student_id,
    s.name AS student_name,
    s.email,
    c.name AS college_name,
    s.year_of_study,
    COUNT(DISTINCT r.id) AS total_registrations,
    COUNT(DISTINCT a.id) AS total_attendances,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT r.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT r.id))
        END, 2
    ) AS attendance_rate,
    GROUP_CONCAT(DISTINCT e.title) AS events_attended
FROM students s
LEFT JOIN registrations r ON s.id = r.student_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON s.id = a.student_id
LEFT JOIN events e ON a.event_id = e.id
INNER JOIN colleges c ON s.college_id = c.id
GROUP BY s.id, s.name, s.email, c.name, s.year_of_study
ORDER BY total_attendances DESC, attendance_rate DESC;

-- ===============================================
-- 6. TOP 3 MOST ACTIVE STUDENTS
-- ===============================================
SELECT 
    s.id AS student_id,
    s.name AS student_name,
    s.email,
    c.name AS college_name,
    COUNT(DISTINCT a.id) AS events_attended,
    COUNT(DISTINCT r.id) AS total_registrations,
    ROUND(AVG(f.rating), 2) AS avg_feedback_given,
    GROUP_CONCAT(DISTINCT e.title) AS attended_events
FROM students s
INNER JOIN attendances a ON s.id = a.student_id
INNER JOIN registrations r ON s.id = r.student_id
INNER JOIN events e ON a.event_id = e.id
INNER JOIN colleges c ON s.college_id = c.id
LEFT JOIN feedback f ON s.id = f.student_id
GROUP BY s.id, s.name, s.email, c.name
ORDER BY events_attended DESC, total_registrations DESC
LIMIT 3;

-- ===============================================
-- 7. FILTER BY EVENT TYPE - WORKSHOP PARTICIPATION
-- ===============================================
SELECT 
    e.event_type,
    COUNT(DISTINCT e.id) AS total_events,
    COUNT(DISTINCT r.student_id) AS unique_participants,
    COUNT(r.id) AS total_registrations,
    COUNT(a.id) AS total_attendances,
    ROUND(AVG(f.rating), 2) AS avg_rating
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON e.id = a.event_id
LEFT JOIN feedback f ON e.id = f.event_id
WHERE e.event_type = 'workshop'
GROUP BY e.event_type;

-- ===============================================
-- 8. COLLEGE-WISE PERFORMANCE SUMMARY
-- ===============================================
SELECT 
    c.id AS college_id,
    c.name AS college_name,
    c.location,
    COUNT(DISTINCT s.id) AS total_students,
    COUNT(DISTINCT e.id) AS events_hosted,
    COUNT(DISTINCT r.id) AS total_registrations,
    COUNT(DISTINCT a.id) AS total_attendances,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT r.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT r.id))
        END, 2
    ) AS college_attendance_rate,
    ROUND(AVG(f.rating), 2) AS avg_feedback_rating
FROM colleges c
LEFT JOIN students s ON c.id = s.college_id
LEFT JOIN events e ON c.id = e.college_id
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON r.student_id = a.student_id AND r.event_id = a.event_id
LEFT JOIN feedback f ON a.student_id = f.student_id AND a.event_id = f.event_id
GROUP BY c.id, c.name, c.location
ORDER BY college_attendance_rate DESC;

-- ===============================================
-- 9. MONTHLY EVENT TRENDS
-- ===============================================
SELECT 
    strftime('%Y-%m', e.event_date) AS event_month,
    COUNT(DISTINCT e.id) AS events_count,
    COUNT(DISTINCT r.id) AS total_registrations,
    COUNT(DISTINCT a.id) AS total_attendances,
    ROUND(AVG(f.rating), 2) AS avg_monthly_rating
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON e.id = a.event_id
LEFT JOIN feedback f ON e.id = f.event_id
WHERE e.event_date >= date('now', '-12 months')
GROUP BY strftime('%Y-%m', e.event_date)
ORDER BY event_month DESC;

-- ===============================================
-- 10. LOW ATTENDANCE EVENTS (< 60% attendance)
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_date,
    c.name AS college_name,
    COUNT(DISTINCT r.id) AS registered,
    COUNT(DISTINCT a.id) AS attended,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT r.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT r.id))
        END, 2
    ) AS attendance_percentage
FROM events e
LEFT JOIN registrations r ON e.id = r.event_id AND r.status = 'confirmed'
LEFT JOIN attendances a ON e.id = a.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_date, c.name
HAVING COUNT(DISTINCT r.id) > 0 
   AND (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT r.id)) < 60
ORDER BY attendance_percentage ASC;

-- ===============================================
-- 11. FEEDBACK ANALYSIS - EVENTS NEEDING IMPROVEMENT
-- ===============================================
SELECT 
    e.id AS event_id,
    e.title AS event_title,
    e.event_type,
    c.name AS college_name,
    COUNT(f.id) AS feedback_count,
    ROUND(AVG(f.rating), 2) AS avg_rating,
    SUM(CASE WHEN f.rating <= 2 THEN 1 ELSE 0 END) AS poor_ratings,
    ROUND(
        (SUM(CASE WHEN f.rating <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(f.id)), 2
    ) AS poor_rating_percentage
FROM events e
INNER JOIN feedback f ON e.id = f.event_id
INNER JOIN colleges c ON e.college_id = c.id
GROUP BY e.id, e.title, e.event_type, c.name
HAVING feedback_count >= 5 AND avg_rating < 3.5
ORDER BY avg_rating ASC, poor_rating_percentage DESC;

-- ===============================================
-- 12. CROSS-COLLEGE PARTICIPATION
-- ===============================================
SELECT 
    student_college.name AS student_college,
    event_college.name AS event_college,
    COUNT(r.id) AS cross_registrations,
    COUNT(a.id) AS cross_attendances
FROM registrations r
INNER JOIN students s ON r.student_id = s.id
INNER JOIN colleges student_college ON s.college_id = student_college.id
INNER JOIN events e ON r.event_id = e.id
INNER JOIN colleges event_college ON e.college_id = event_college.id
LEFT JOIN attendances a ON r.student_id = a.student_id AND r.event_id = a.event_id
WHERE s.college_id != e.college_id  -- Only cross-college registrations
AND r.status = 'confirmed'
GROUP BY student_college.name, event_college.name
ORDER BY cross_registrations DESC;