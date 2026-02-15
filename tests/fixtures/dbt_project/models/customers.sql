-- Sample customers model
-- Selects and transforms customer data from the seed

select
    customer_id,
    first_name,
    last_name,
    email,
    created_at
from {{ ref('customers_seed') }}
