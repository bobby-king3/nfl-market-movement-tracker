{% macro implied_probability(column_name) %}
    case
        when {{ column_name }} < 0 then abs({{ column_name }}) / (abs({{ column_name }}) + 100)
        when {{ column_name }} > 0 then 100.0 / ({{ column_name }} + 100)
    end
{% endmacro %}
