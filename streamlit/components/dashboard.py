import streamlit as st

from queries.questions import execute_question, supported_questions
from utils.bigquery_client import query
from utils.config import table_name


def render_dashboard() -> None:
    st.title("Cafeteria waste overview")
    try:
        daily, category, monthly = (table_name(t) for t in ("daily_waste_summary", "category_waste_summary", "monthly_waste_summary"))
        kpis = query(f"SELECT SUM(total_food_waste_kg) total_waste, SUM(total_meals_served) meals, SAFE_DIVIDE(SUM(total_food_waste_kg),SUM(total_meals_served)) per_meal FROM {daily}")
        categories = query(f"SELECT COUNT(*) AS n FROM {category}")
        if kpis.empty or kpis.iloc[0]["total_waste"] is None:
            st.info("No transformed warehouse records yet. Run the pipeline to populate the dashboard.")
            return
        waste, meals, per_meal = kpis.iloc[0]
        a, b, c, d = st.columns(4)
        a.metric("Total food waste", f"{waste:,.1f} kg")
        b.metric("Meals served", f"{meals:,.0f}")
        c.metric("Waste per meal", f"{per_meal:.3f} kg")
        d.metric("Categories", int(categories.iloc[0]["n"]))
        daily_data = query(f"SELECT waste_date, total_food_waste_kg FROM {daily} ORDER BY waste_date")
        category_data = query(f"SELECT waste_category, total_food_waste_kg FROM {category} ORDER BY total_food_waste_kg DESC")
        monthly_data = query(f"SELECT waste_month, total_food_waste_kg FROM {monthly} ORDER BY waste_month")
        left, right = st.columns(2)
        with left:
            st.subheader("Daily waste trend")
            st.line_chart(daily_data.set_index("waste_date"))
        with right:
            st.subheader("Waste by category")
            st.bar_chart(category_data.set_index("waste_category"))
        st.subheader("Monthly waste trend")
        st.line_chart(monthly_data.set_index("waste_month"))
        st.subheader("Daily summary")
        st.dataframe(daily_data, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"Unable to load BigQuery analytics. Check credentials, datasets, and dbt output. Details: {exc}")


def render_conversation() -> None:
    st.title("Ask about cafeteria waste")
    st.caption("Ask one of the supported questions below. Queries are predefined and run against dbt analytics tables.")
    questions = supported_questions()
    with st.expander("Supported questions", expanded=True):
        for item in questions:
            st.markdown(f"- {item.label}")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for role, message, sql, result, chart in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)
            if sql:
                st.code(sql, language="sql")
            if result is not None:
                st.dataframe(result, use_container_width=True, hide_index=True)
                if chart and not result.empty and len(result.columns) >= 2:
                    if chart == "scatter":
                        st.scatter_chart(result, x=result.columns[0], y=result.columns[1])
                    elif chart == "line":
                        st.line_chart(result.set_index(result.columns[0]))
                    else:
                        st.bar_chart(result.set_index(result.columns[0]))
    prompt = st.chat_input("Ask a supported food waste question")
    if prompt:
        question = next((q for q in questions if q.label.casefold() == prompt.strip().casefold()), None)
        st.session_state.chat_history.append(("user", prompt, None, None, None))
        if question is None:
            st.session_state.chat_history.append(("assistant", "I can answer one of the six supported questions listed above. Please use one of those questions.", None, None, None))
        else:
            try:
                result = execute_question(question)
                answer = "Here are the results." if not result.empty else "The warehouse returned no rows for this question."
                st.session_state.chat_history.append(("assistant", answer, question.sql, result, question.chart))
            except Exception as exc:
                st.session_state.chat_history.append(("assistant", f"The BigQuery query could not be completed. Check credentials and analytics tables. Details: {exc}", question.sql, None, None))
        st.rerun()
