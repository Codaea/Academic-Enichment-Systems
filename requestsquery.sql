-- SQLite
SELECT masterschedule.*, (
            SELECT requests.requested_rooms
            FROM requests
            WHERE requests.studentId = masterschedule.studentId
            ) AS matched_value
            FROM masterschedule
            WHERE masterschedule.period1 = 103;