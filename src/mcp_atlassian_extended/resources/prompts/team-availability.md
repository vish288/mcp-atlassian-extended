# Team availability: $start_date to $end_date

## Team Members
$team_members

## Steps

1. **Check who is out** — use `confluence_get_time_off` for the period $start_date to $end_date with `group_by_person=true` to get an overview of team absences.
2. **Get per-person details** — call `confluence_get_time_off` with `person` set to a team member's full name to retrieve:
   - Vacation days
   - Sick leave
   - Public holidays
   - Other absences
3. **Calculate capacity** — use `confluence_sprint_capacity` (pass `team_members`, `sprint_start`, `sprint_end`) to compute:
   - Available working days per person
   - Total team capacity (in person-days)
   - Percentage reduction from full capacity
4. **Identify conflicts** — flag:
   - Days when more than 50% of the team is out
   - Periods with no coverage for critical roles
   - Overlapping absences that may impact deliverables
5. **Summary report** — present:
   - Per-person availability table (available days / total days)
   - Team capacity percentage
   - Risk periods requiring mitigation
   - Recommendations for scheduling key meetings or reviews
