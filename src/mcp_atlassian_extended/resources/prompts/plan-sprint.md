# Plan sprint $sprint_id on board $board_id

## Steps

1. **Get sprint details** — use `jira_get_sprint` with sprint_id="$sprint_id" to check the sprint name, start/end dates, and current state.
2. **Get board config** — use `jira_get_board` with board_id="$board_id" to understand the board type and project.
3. **Check team availability** — use `confluence_sprint_capacity` to calculate available capacity for the sprint period, accounting for holidays and time-off.
4. **Review backlog** — use `jira_backlog` with board_id="$board_id" to get prioritized backlog items. Note story points and priorities.
5. **Calculate scope** — based on:
   - Team velocity (average of last 3 sprints)
   - Available capacity from step 3
   - Carry-over items from the previous sprint
6. **Suggest sprint scope** — recommend which backlog items to pull into the sprint:
   - Start with highest priority items
   - Respect capacity limits
   - Ensure a mix of features, bugs, and tech debt
   - Flag items missing estimates or acceptance criteria
7. **Move issues** — use `jira_move_to_sprint` to move accepted items into sprint $sprint_id.
8. **Summary** — report:
   - Total story points committed
   - Capacity utilization percentage
   - Risk items (large stories, dependencies, missing info)
