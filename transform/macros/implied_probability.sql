{% macro implied_probability(column_name) %}
    case
        when {{ column_name }} < 0 then round(abs({{ column_name }}) / (abs({{ column_name }}) + 100), 4)
        when {{ column_name }} > 0 then round(100.0 / ({{ column_name }} + 100), 4)
    end
{% endmacro %}
