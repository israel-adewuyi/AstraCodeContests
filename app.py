import streamlit as st
import json
from typing import Dict
from dataclasses import asdict
from contest_manager import ContestManager, ContestConfig, ContestStatus
from utils import extract_python_code

# Initialize session state for ContestManager
if 'contest_manager' not in st.session_state:
    config = ContestConfig(contest_id=410)
    st.session_state.contest_manager = ContestManager(config)

# Streamlit app
st.title("AstraContest Interface")

# Create tabs for adding problems and viewing problems
tab1, tab2 = st.tabs(["Add Problem", "View Problems"])

with tab1:
    st.header("Add New Problem")
    with st.form("problem_form"):
        statement = st.text_area("Problem Statement", height=150)
        input_spec = st.text_area("Input Specification", height=100)
        output_spec = st.text_area("Output Specification", height=100)
        contest_id = st.number_input("Contest ID", min_value=1, value=410)
        problem_id = st.text_input("Problem ID", value="A")
        examples_input = st.text_area("Examples (JSON format)", 
                                    value='[{"input": ["5\\n3 1 4 1 5\\n4"], "output": ["2"]}]')
        num_solutions = st.number_input("Number of Solutions", min_value=1, max_value=16384, value=8)
        
        submitted = st.form_submit_button("Add Problem")
        
        if submitted:
            try:
                # Parse examples JSON
                examples = json.loads(examples_input)
                
                problem_data = {
                    "statement": statement,
                    "input_specification": input_spec,
                    "output_specification": output_spec,
                    "contest_id": contest_id,
                    "problem_id": problem_id,
                    "examples": examples,
                    "num_solutions": num_solutions
                }
                
                problem_key = st.session_state.contest_manager.add_problem(problem_data)
                st.success(f"Problem {problem_key} added successfully!")
                
            except json.JSONDecodeError:
                st.error("Invalid JSON format in examples")
            except Exception as e:
                st.error(f"Error adding problem: {str(e)}")

with tab2:
    st.header("Current Problems")
    if st.session_state.contest_manager.problems:
        for problem_key, problem in list(st.session_state.contest_manager.problems.items()):
            col1, col2 = st.columns([10, 1])
            with col1:
                with st.expander(f"Problem {problem_key}"):
                    st.write(f"**Statement:** {problem.statement}")
                    st.write(f"**Input Specification:** {problem.input_specification}")
                    st.write(f"**Output Specification:** {problem.output_specification}")
                    st.write(f"**Contest ID:** {problem.contest_id}")
                    st.write(f"**Problem ID:** {problem.problem_id}")
                    st.write("**Examples:**")
                    st.json(problem.examples)
                    st.write(f"**Number of solutions:** {problem.num_solutions}")
                    
                    if st.button(f"Solve Problem {problem_key}", key=f"solve_{problem_key}"):
                        with st.spinner(f"Solving problem {problem_key}..."):
                            result = st.session_state.contest_manager.solve_problem(problem_key)
                            if isinstance(result, dict) and result.get("status") == "failed":
                                st.error(f"Failed to solve problem {problem_key}: {result.get('reason')}")
                            else:
                                st.success(f"Problem {problem_key} solved successfully!")
                                st.write("**Selected Solution:**")
                                selected = result.get("selected_solution", {})
                                solution_id = selected.get("selected_solution_id")
                                code = extract_python_code(selected.get("generation", ""))
                                if solution_id:
                                    st.write(f"**Solution ID:** `{solution_id}`")
                                if code:
                                    st.code(code, language="python")
                    if st.button(f"Show Solution {problem_key}", key=f"show_solution_{problem_key}"):
                        selected_solution = st.session_state.contest_manager.selected_solutions.get(problem_key)
                        if selected_solution and selected_solution.get("generation"):
                            code = extract_python_code(selected_solution.get("generation", ""))
                            if code:
                                st.write("**Selected Solution:**")
                                st.code(code, language="python")
                            else:
                                st.info("No solutions yet.")
                        else:
                            st.info("No solutions yet.")
            with col2:
                if st.button("❌", key=f"delete_{problem_key}"):
                    st.session_state.contest_manager.delete_problem(problem_key)
                    st.rerun()
                # Add Edit button
                if st.button("✏️", key=f"edit_{problem_key}"):
                    st.session_state[f"edit_modal_{problem_key}"] = True
            # Show modal if edit button was clicked
            if st.session_state.get(f"edit_modal_{problem_key}", False):
                with st.expander("Edit Problem ...", expanded=True):
                    edit_statement = st.text_area("Statement", value=problem.statement, key=f"edit_statement_{problem_key}")
                    edit_input_spec = st.text_area("Input Specification", value=problem.input_specification, key=f"edit_input_spec_{problem_key}")
                    edit_output_spec = st.text_area("Output Specification", value=problem.output_specification, key=f"edit_output_spec_{problem_key}")
                    edit_examples = st.text_area("Examples (JSON format)", value=json.dumps(problem.examples, indent=2), key=f"edit_examples_{problem_key}")
                    edit_num_solutions = st.number_input("Number of Solutions", min_value=1, max_value=16384, value=problem.num_solutions, key=f"edit_num_solutions_{problem_key}")
                    submitted_edit = st.button("Save Changes", key=f"submit_edit_{problem_key}")
                    cancel_edit = st.button("Cancel", key=f"cancel_edit_{problem_key}")
                    if submitted_edit:
                        try:
                            new_examples = json.loads(edit_examples)
                            updated_data = {
                                "statement": edit_statement,
                                "input_specification": edit_input_spec,
                                "output_specification": edit_output_spec,
                                "examples": new_examples,
                                "num_solutions": edit_num_solutions
                            }
                            st.session_state.contest_manager.update_problem(problem_key, updated_data)
                            st.success("Problem updated!")
                            st.session_state[f"edit_modal_{problem_key}"] = False
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format in examples")
                        except Exception as e:
                            st.error(f"Error updating problem: {str(e)}")
                    if cancel_edit:
                        st.session_state[f"edit_modal_{problem_key}"] = False
                        st.rerun()
    else:
        st.info("No problems added yet.")
        
    if st.button("Solve All Problems Concurrently"):
        st.session_state.contest_manager.solve_all_problems_concurrently()
        st.success("Started solving all problems concurrently!")

    # progress = st.session_state.contest_manager.get_progress()
    # for problem_key, prog in progress.items():
    #     st.write(f"Problem {problem_key}: {prog.get('status', 'pending')}")
    #     if 'detail' in prog:
    #         selected = prog['detail'].get('selected_solution', {}) if isinstance(prog['detail'], dict) else {}
    #         solution_id = selected.get('selected_solution_id')
    #         code = extract_python_code(selected.get('generation', ""))
    #         if solution_id:
    #             st.write(f"**Solution ID:** `{solution_id}`")
    #         if code:
    #             st.code(code, language="python")

    if st.button("Refresh Progress"):
        # st.rerun()
        progress = st.session_state.contest_manager.get_progress()
        for problem_key, prog in progress.items():
            st.write(f"Problem {problem_key}: {prog.get('status', 'pending')}")
            if 'detail' in prog:
                selected = prog['detail'].get('selected_solution', {}) if isinstance(prog['detail'], dict) else {}
                solution_id = selected.get('selected_solution_id')
                code = extract_python_code(selected.get('generation', ""))
                if solution_id:
                    st.write(f"**Solution ID:** `{solution_id}`")
                if code:
                    st.code(code, language="python")
    
    if st.button("Reset Solution"):
        st.session_state.contest_manager.reset_solution()
        