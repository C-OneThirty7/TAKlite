# TAKlite Access Control Guide

Version: TAKlite v0.2.24

## Purpose

This guide explains how TAKlite controls who can see Position Location Information (PLI), who can send datapackages, and who can receive datapackages.

The current access model is intentionally simple:

```text
Team boundary first
Level second
Access override only when needed
Team links only when teams should interact
```

For most users, admins should assign only:

- Team
- Level

Most users do not need an access override.

## Default Open Mode

TAKlite stays open until access policy is actually assigned.

That means:

- New server with no team assignments: users can see and send normally.
- Teams created but nobody assigned yet: users can still see and send normally.
- Once users are assigned to teams, team and level rules begin shaping traffic.

This keeps a simple TAKlite relay easy to use while still allowing controlled visibility when an admin needs it.

## Core Terms

### Connection User

A Connection User is a TAKlite user profile with an ATAK/WinTAK connection package.

Connection users are created in the `Users` panel and managed in the `Access` panel.

### Team

A Team is the main visibility boundary.

Examples:

```text
Alpha
Bravo
Charlie
Staff
Visitors
```

Users in the same team can see, send, and receive according to their level.

Users in different teams cannot see, send, or receive across those teams unless a team link or access override allows it.

### Level

Levels are numeric access ranks from 1 to 4.

Levels apply only after the team path is allowed.

```text
Level 1 sees/sends to Level 1
Level 2 sees/sends to Level 2 and Level 1
Level 3 sees/sends to Level 3, Level 2, and Level 1
Level 4 sees/sends to Level 4, Level 3, Level 2, and Level 1
```

Level does not jump team boundaries.

Example:

```text
Alpha Level 4 cannot see Bravo Level 1
unless Alpha is linked to Bravo
or the Alpha user has an access override that allows all teams.
```

### Team User

`Team User` is the default access type.

A Team User:

- Uses assigned teams as the boundary
- Uses level for rank filtering inside allowed teams
- Does not have global powers

This is the correct access type for normal users.

### Access Override

An Access Override is an advanced template for high-trust users.

Use overrides for users who need capabilities beyond normal team and level rules.

Examples:

```text
Controller
Instructor
Safety
Admin
Observer
```

Overrides can grant broad powers such as:

- See all teams
- Send to all teams
- Receive from all teams
- See assigned teams
- Send to assigned teams
- Receive from assigned teams

Important: an override controls what that user can do. It does not automatically make that user visible to everyone else.

## The Most Important Rule

Team boundaries come first.

Levels only apply after the team path is allowed.

This means:

```text
Team A Level 4 cannot see Team B Level 1 by level alone.
```

To make Team A interact with Team B, use a Team Link or an Access Override.

## Level Example

Scenario:

- Controller users have an override for `See all teams` and `Send to all teams`.
- Controllers are Level 4.
- Team A users are Team Users.
- Team A users are Level 1.

Result:

- Controllers can see Team A users.
- Controllers can send to Team A users.
- Team A users cannot see Controllers unless their own team/link/override/level path allows it.
- Team A users cannot send to Controllers unless their own policy allows it.

This supports the common pattern:

```text
High-trust users see everyone.
Normal users do not automatically see high-trust users.
```

## Team Links

Team Links connect separate teams.

No link means separate teams stay separate.

Team links can be one-way or two-way.

### No Link

```text
Alpha    Bravo
```

Alpha and Bravo stay isolated.

### One-Way Link

```text
Alpha -> Bravo
```

Alpha users can interact with Bravo users according to level.

Bravo users do not automatically interact with Alpha users.

### Two-Way Link

```text
Alpha <-> Bravo
```

Both teams can interact according to level.

## Datapackage Behavior

TAKlite enforces the same access policy on datapackage search, query, download, and plugin-controlled send operations.

The backend policy is the failsafe:

- If a user should not see a package, it should not appear in their query/search results.
- If a user tries to download a blocked package, TAKlite should deny it.
- If a user sends through the Axon plugin, TAKlite checks the requested audience before delivery.

The Axon plugin can provide a pre-send review, but TAKlite still enforces policy server-side.

## Recommended Admin Workflow

Use this order:

1. Create teams.
2. Create users.
3. Bulk assign users to teams.
4. Bulk set levels.
5. Leave most users as `Team User`.
6. Create access overrides only for controller/admin-style users.
7. Link teams only when cross-team interaction is needed.
8. Use Access Preview before field testing.

## Creating Users

In `Users`:

1. Create a single user or bulk users.
2. Leave `Access type` as `Team User (default)` unless the user needs special powers.
3. Set the user's level, usually Level 1 for normal users.
4. Assign teams directly during creation or later in `Access`.

TAKlite learns IP/device details from TAK/Axon traffic when possible. Admins can edit those fields later if needed.

## Bulk Membership

`Bulk Membership` is the primary admin workflow for many users.

Use it to:

- Select several users at once
- Replace/add/remove teams
- Set levels
- Set an access override
- Clear an access override back to Team User

### Bulk Access Type Actions

```text
Leave access type unchanged
```

Does not change whether selected users are Team Users or have an override.

```text
Set to Team User
```

Clears any existing access override.

```text
Set override
```

Applies the selected access override.

### Bulk Team Actions

```text
Replace teams
```

Removes existing team membership and applies the selected teams.

```text
Add teams
```

Keeps existing teams and adds the selected teams.

```text
Remove teams
```

Removes only the selected teams.

## Individual Membership

Use `Individual Membership` when one user needs a manual correction.

You can edit:

- Access type
- Level
- Teams

Use this for cleanup, not primary onboarding.

## Access Preview

Access Preview is the admin's sanity check.

Pick a user and verify:

- Who they can see
- Who they can send to
- Who can see them
- Who can send to them

Use Access Preview before issuing users their final connection packages.

## Example 1: Two Isolated Teams

Goal:

- Alpha sees Alpha only.
- Bravo sees Bravo only.

Setup:

```text
Teams:
  Alpha
  Bravo

Alpha users:
  Access type: Team User
  Team: Alpha
  Level: 1

Bravo users:
  Access type: Team User
  Team: Bravo
  Level: 1

Team links:
  none
```

Result:

- Alpha users see Alpha users.
- Bravo users see Bravo users.
- Alpha and Bravo do not see each other.

## Example 2: Controllers See Everyone

Goal:

- Controllers see all teams.
- Normal users do not see controllers.

Setup:

```text
Access override:
  Name: Controller
  See all teams: On
  Send to all teams: On
  Receive from all teams: On

Controller users:
  Access type: Controller
  Level: 4
  Team: optional

Normal users:
  Access type: Team User
  Level: 1
  Team: Alpha or Bravo
```

Result:

- Controllers see Alpha and Bravo.
- Controllers can send to Alpha and Bravo.
- Alpha/Bravo users do not automatically see controllers.

## Example 3: Temporary Cross-Team Visibility

Goal:

- Alpha and Bravo are normally isolated.
- For one event, Alpha and Bravo need to interact.

Setup:

```text
Before event:
  No link between Alpha and Bravo

During event:
  Team Link: Alpha <-> Bravo

After event:
  Set link back to No Link
```

Result:

- Teams can be merged or split without editing every user.
- Levels still apply across the linked path.

## Example 4: One-Way Observation

Goal:

- Staff can see Student Team.
- Student Team cannot see Staff.

Setup:

```text
Staff users:
  Access type: Controller or Staff override
  Level: 4

Student users:
  Access type: Team User
  Team: Student Team
  Level: 1
```

Result:

- Staff sees students.
- Students do not see staff.

Alternate setup:

```text
Teams:
  Staff
  Student Team

Team Link:
  Staff -> Student Team
```

This keeps Staff as Team Users but still allows one-way team visibility.

## Example 5: Mixed Levels Inside One Team

Goal:

- Team Lead sees everyone in Alpha.
- Alpha members do not all see the Team Lead.

Setup:

```text
Team Lead:
  Access type: Team User
  Team: Alpha
  Level: 4

Alpha normal users:
  Access type: Team User
  Team: Alpha
  Level: 1
```

Result:

- Team Lead sees all Alpha users.
- Level 1 users see other Level 1 users.
- Level 1 users do not see the Level 4 Team Lead.

## Common Mistakes

### Mistake: Giving Everyone An Override

Most users should be Team Users.

Use overrides only for users who need broad power.

### Mistake: Expecting Level To Cross Teams

Level does not cross teams by itself.

Use Team Links or an override for cross-team behavior.

### Mistake: Forgetting Access Preview

Always preview one representative user from each team before field use.

## Quick Checklist

Before handing out connection packages:

- Teams created
- Users assigned to correct teams
- Users assigned to correct levels
- Normal users left as Team User
- Controller/admin users given the intended override
- Team links set only where needed
- Access Preview checked for each team
- Test two real TAK clients before scaling up

