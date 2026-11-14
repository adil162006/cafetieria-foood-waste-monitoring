select *
from {{ ref('stg_food_waste') }}
where (meals_served is not null and meals_served < 0)
   or (kitchen_staff is not null and kitchen_staff < 0)
   or (humidity_percent is not null and (humidity_percent < 0 or humidity_percent > 100))
   or (day_of_week is not null and day_of_week not between 0 and 6)
   or (special_event is not null and special_event not in (0, 1))
   or (past_waste_kg is not null and past_waste_kg < 0)
