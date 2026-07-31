# TAKlite Access Control Guide

Version: TAKlite v0.2.23

## Purpose

This guide explains how TAKlite roles, groups, and visibility links work, and how an admin can use them to control who can see whom on the map and who can send data to whom.

TAKlite access control is designed for small teams that need simple, fast changes during training, field work, or events. The goal is to let an admin build common patterns such as:

- Alpha team sees Alpha only.
- Bravo team sees Bravo only.
- Instructors see everyone.
- Normal users do not see instructors unless the admin wants that.
- Isolated users can be visible to instructors while seeing nobody.
- Teams can be temporarily linked together and split apart again.

## Quick Mental Model

Think of TAKlite access control in three layers:

```text
Role   = what broad powers a user has
Group  = what team or visibility bucket a user belongs to
Link   = whether one group can see/send to, and be received by, another group
```

Each connection user can have:

- One role
- Zero, one, or many groups
- Visibility created by shared groups, role powers, and cross-group links

The best workflow is:

1. Create groups first.
2. Create roles second.
3. Assign users to roles and groups.
4. Add links only when groups need cross-group visibility.
5. Use Access Preview to verify the outcome.

## Default Open Mode

TAKlite is open by default until an admin actually assigns access policy to users.

That means if you create connection users and do not assign any roles, groups, or group links, active users can see each other, send CoT traffic, chat, and use normal datapackage visibility. This is intentional. A simple TAKlite install should work like a normal relay without forcing the admin to build an access-control policy first.

Access rules begin shaping traffic after policy is assigned. In practice, TAKlite treats the policy as active when at least one active user has a role, at least one user is placed in a group, or at least one group link exists.

Operationally:

- No roles/groups assigned: everyone sees everyone.
- Roles/groups created but not assigned to users: everyone still sees everyone.
- At least one user assigned a role or group: access policy is active.
- Once policy is active, unassigned users should be treated as incomplete setup and may not see other users as expected.

If you want an open server, leave users unassigned in the Access panel. If you want controlled visibility, assign every operational user to the intended role and group, then verify with Access Preview.

## Important Terms

### Connection User

A Connection User is a TAKlite user profile that receives a `.dp.zip` connection package for ATAK or WinTAK. These are the users who appear in the Access panel.

### Role

A role defines broad permission behavior. Examples:

- Admin
- Instructor
- Student
- Observer
- Isolated

Role names are yours to choose. TAKlite does not require names like Instructor or Student. The behavior comes from the checkboxes assigned to the role.

### Group

A group is a team, class, cell, or visibility bucket. Examples:

- Alpha
- Bravo
- Charlie
- Staff
- Beacon

Groups are not permission levels by themselves. They are membership buckets. The permissions come from a user's role and from links between groups.

### Link

A link controls cross-group visibility, send ability, and receive ability.

No link means groups stay isolated from each other unless a user's role has a global permission such as "Can see everyone."

Links are directional:

```text
Alpha -> Bravo
```

means Alpha can see Bravo, send to Bravo, and Bravo can receive that path. Bravo does not automatically see or send to Alpha.

```text
Two Way
```

means Alpha and Bravo can see, send, and receive both directions.

## Role Permissions

Roles have four permission switches.

### Can See Everyone

This user can see all active TAKlite users, regardless of group.

Use this for admins, instructors, safety monitors, or command staff.

Important: this does not automatically make the admin visible to everyone else. It only controls what the admin can see.

### Can Send To Everyone

This user can send data to all active TAKlite users, regardless of group.

Use this for admins or instructors who need to send datapackages or server-routed information to everyone.

### Can See Assigned Groups

This user can see other users who share at least one group with them.

Use this for normal team members.

Example:

```text
User A groups: Alpha
User B groups: Alpha
User C groups: Bravo
```

If User A has "Can see assigned groups", User A can see User B. User A cannot see User C unless Alpha and Bravo are linked or User A has "Can see everyone."

### Can Send To Assigned Groups

This user can send to other users who share at least one group with them.

Use this for normal team members who should send datapackages or server-routed data to teammates.

## Recommended Base Roles

These examples are starting points. Rename them to fit your environment.

### Admin Or Instructor Role

Use for users who should see and send to everyone.

```text
Can see everyone:        On
Can send to everyone:    On
Can see assigned groups: Optional
Can send assigned groups: Optional
```

Notes:

- Admins do not need to be placed in every group.
- Admins can see isolated groups such as Beacon even if Beacon cannot see anyone.
- Other users do not see admins unless their own role/group/link settings allow it.

### Team Member Role

Use for normal users who should see and send within their own team.

```text
Can see everyone:        Off
Can send to everyone:    Off
Can see assigned groups: On
Can send assigned groups: On
```

Notes:

- Team members see people who share at least one group.
- Team members do not see other teams unless the groups are linked.

### Observer Role

Use for users who should see their assigned group but not send to it.

```text
Can see everyone:        Off
Can send to everyone:    Off
Can see assigned groups: On
Can send assigned groups: Off
```

### Isolated Role

Use for users who should not see or send to anyone by default.

```text
Can see everyone:        Off
Can send to everyone:    Off
Can see assigned groups: Off
Can send assigned groups: Off
```

Notes:

- This is useful for Beacon, role-player, hidden target, or evaluator profiles.
- Admins with "Can see everyone" can still see isolated users.
- Isolated users will not see admins unless you intentionally give them visibility.

## Recommended Group Patterns

### Team Groups

Use team groups for normal visibility:

```text
Alpha
Bravo
Charlie
Delta
```

Assign each user to their team group.

### Staff Or Admin Group

Use a Staff or Admin group only when you want staff to see each other through normal group membership.

Admins do not need to be in a Staff group to see everyone if their role already has "Can see everyone."

### Beacon Or Hidden Group

Use a Beacon group for users who should be visible to admins but hidden from students.

Recommended:

```text
Beacon users:
  Role: Isolated
  Group: Beacon

Admin users:
  Role: Admin or Instructor
  Group: optional
```

Do not link Beacon to student groups unless students should see Beacon.

## How Visibility Is Decided

When TAKlite decides whether User A can see User B, it checks:

1. Is User A looking at themselves? If yes, allowed.
2. Does User A's role have "Can see everyone"? If yes, allowed.
3. Does User A's role have "Can see assigned groups", and do User A and User B share a group? If yes, allowed.
4. Is there a link from one of User A's groups to one of User B's groups with see enabled? If yes, allowed.
5. Otherwise, not allowed.

Send permission works the same way, but uses the send switches and send links. Receive permission is checked separately for datapackages, so a recipient can be allowed to see a sender while still refusing package delivery from that sender.

## How Access Levels Work

Access levels are optional. If a user has no level assigned, TAKlite keeps using the normal role/group/link rules.

When levels are assigned, they act like a simple ladder inside the permissions that already exist:

- Level 1 can see/send Level 1.
- Level 2 can see/send Level 2 and Level 1.
- Level 3 can see/send Level 3, Level 2, and Level 1.
- Level 4 can see/send Level 4, Level 3, Level 2, and Level 1.

Receiving is not limited by the recipient's level. This allows a Level 1 user to receive a package sent by a Level 4 user when the sender, receiver, role, and group rules allow that path.

Groups still matter. A Level 4 user in Alpha does not automatically see Bravo unless their role can see everyone or Alpha is linked to Bravo.

Use levels when a team needs rank-based visibility inside the same group. Use roles for broad powers such as "can see everyone". Use groups for team membership.

## How Datapackage Visibility Works

Access control also affects datapackage visibility when enforcement is enabled.

In general:

- Public datapackages are visible to users.
- Private datapackages are visible to the creator.
- A private package from another user is visible when the requester can see the creator, the creator can send to the requester, and the requester can receive from the creator.
- Admins with broad see/send roles can manage packages from the admin panel.

Filename tags can narrow who sees a package uploaded from ATAK/WinTAK without changing the TAK client.

Examples:

```text
maps__lvl4ONLY.dp.zip
maps__lvl4ALL.dp.zip
brief__lvl4and2ONLY.dp.zip
```

The tag behavior is:

- `lvl4ONLY` means only Level 4 users can query/download that package.
- `lvl4ALL` means Levels 4, 3, 2, and 1 can query/download that package.
- `lvl4and2ONLY` means only Level 4 and Level 2 users can query/download that package.
- Untagged packages follow the sender's normal role/group/link visibility policy.

TAKlite still enforces the sender and receiver policy after reading the filename tag. For example, an Alpha package tagged `lvl4ONLY` is limited to allowed Level 4 users; it does not automatically cross into Bravo unless the role/group/link policy allows that path.

TAKlite also prevents lower-level users from creating higher-level tagged packages. For example, a Level 2 user cannot upload a package named `brief__lvl4ONLY.dp.zip`.

If datapackage behavior feels unexpected, use Access Preview first. If the two users do not appear in the expected "Can See", "Can Send To", "Seen By", or "Can Receive From" lists, adjust roles/groups/links before retesting in ATAK.

## Admin Package Send

The Datapackages panel can upload a `.zip` or `.dp.zip` from the admin computer and can send any stored package to selected connection users.

The normal workflow is:

1. Open Datapackages.
2. Upload the file, or choose an existing stored package.
3. Use Send to select online or offline connection users.
4. Review the send result for sent, pending, blocked, or failed targets.

The admin send action checks the same rules:

1. The package creator must be allowed to send to the selected user.
2. The selected user must be allowed to receive from the package creator.
3. Explicit recipient lists, when present, limit package query/download to the selected users and the creator.

If the selected user is online, TAKlite sends the file-share notification immediately. If the selected user is offline, TAKlite records the delivery as pending and tries to push the notification when that user reconnects.

The send result explains each target:

- `sent` means the connected client socket accepted the file-share notification.
- `pending_offline` means the user is allowed but not currently connected.
- `blocked_sender_policy` means the package creator cannot send to the selected user.
- `blocked_receive_policy` means the selected user cannot receive from the package creator.
- `blocked_explicit_audience` means the selected user is outside that package's explicit recipient list.
- `blocked_receive_policy` means the selected user cannot receive from the package creator.

## Access Enforcement

Access rules matter when Access Enforcement is on.

Check this in:

```text
Settings -> Access Enforcement
```

Recommended production setting:

```text
Access Enforcement: On
```

If Access Enforcement is off, the Access panel can still be configured, but TAKlite will not fully apply the policy to live traffic and package visibility. Use off only for testing or troubleshooting.

## The Access Panel

Open:

```text
TAKlite Admin -> Access
```

The panel is organized into these sections.

### User Membership

Use this to edit one user at a time.

For each user, choose:

- Role
- One or more groups

Click Save for that user.

Use this when correcting one profile or verifying a special user.

### Bulk Membership

Use this for normal administration.

Bulk Membership lets you:

- Filter users by username, display name, role, or group
- Select many users
- Apply one role to the selected users
- Replace, add, or remove groups for the selected users

Group actions:

```text
Replace groups = remove current groups and set exactly the selected groups
Add groups     = keep current groups and add the selected groups
Remove groups  = remove only the selected groups
```

Use Replace when assigning a class or team from scratch. Use Add when temporarily adding users to another team. Use Remove when ending a temporary assignment.

### Access Preview

Access Preview is the most important verification tool.

Pick a user and check:

```text
Can See
Can Send To
Seen By
Can Receive From
```

Use this before handing devices to users.

### Role Permissions

Create or edit roles here.

Role changes affect every user with that role.

### Groups

Create or edit groups here.

Group changes affect membership buckets. Deleting a group removes membership and links for that group.

### Visibility Links

Use this only when separate groups need cross-group access.

Available modes for each pair:

```text
No Link       = neither group gets cross-group access
Alpha -> Bravo = Alpha can see/send Bravo
Bravo -> Alpha = Bravo can see/send Alpha
Two Way       = both groups can see/send each other
```

## Example 1: Two Student Teams, Instructors See All

Goal:

- Alpha sees Alpha only.
- Bravo sees Bravo only.
- Instructors see Alpha and Bravo.
- Students do not see instructors.

Create roles:

```text
Instructor:
  Can see everyone: On
  Can send to everyone: On
  Can see assigned groups: Off or On
  Can send assigned groups: Off or On

Student:
  Can see everyone: Off
  Can send to everyone: Off
  Can see assigned groups: On
  Can send assigned groups: On
```

Create groups:

```text
Alpha
Bravo
```

Assign users:

```text
Lead Admin:
  Role: Instructor
  Groups: none, or Staff if you want staff grouping

Assistant Admin:
  Role: Instructor
  Groups: none, or Staff

Alpha students:
  Role: Student
  Groups: Alpha

Bravo students:
  Role: Student
  Groups: Bravo
```

Links:

```text
Alpha <-> Bravo: No Link
```

Preview:

- Lead Admin can see everyone.
- Assistant Admin can see everyone.
- Alpha students can see Alpha students.
- Bravo students can see Bravo students.
- Alpha students cannot see Bravo students.
- Students do not see Lead Admin or Assistant Admin unless you put Lead Admin/Assistant Admin into a group visible to students.

## Example 2: Temporarily Merge Alpha And Bravo

Goal:

- Alpha and Bravo usually stay separate.
- During one exercise, they should see and send to each other.
- After the exercise, split them again.

Keep roles and groups the same.

During the exercise:

```text
Visibility Links:
  Alpha <-> Bravo: Two Way
```

After the exercise:

```text
Visibility Links:
  Alpha <-> Bravo: No Link
```

This is faster than moving every user into a new group.

## Example 3: One-Way Visibility

Goal:

- Alpha can see/send Bravo.
- Bravo cannot see/send Alpha.

Use:

```text
Visibility Links:
  Alpha -> Bravo
```

This can be useful when one group is supervising another but should not be exposed in reverse.

Preview:

- An Alpha user should list Bravo users under Can See and Can Send To.
- A Bravo user should not list Alpha users unless another role or group rule allows it.

## Example 4: Beacon Group

Goal:

- Beacons do not see anyone.
- Students do not see Beacons.
- Instructors see Beacons.
- Sometimes students may see Beacons.

Create roles:

```text
Instructor:
  Can see everyone: On
  Can send to everyone: On

Student:
  Can see assigned groups: On
  Can send assigned groups: On

Beacon:
  Can see everyone: Off
  Can send everyone: Off
  Can see assigned groups: Off
  Can send assigned groups: Off
```

Create groups:

```text
Alpha
Bravo
Beacon
```

Assign users:

```text
Beacon users:
  Role: Beacon
  Groups: Beacon

Students:
  Role: Student
  Groups: Alpha or Bravo

Instructors:
  Role: Instructor
  Groups: optional
```

Links:

```text
Beacon <-> Alpha: No Link
Beacon <-> Bravo: No Link
Alpha <-> Bravo: whatever the exercise needs
```

Result:

- Beacons see nobody.
- Students do not see Beacons.
- Instructors see Beacons because Instructor can see everyone.

To temporarily let Alpha see Beacons:

```text
Visibility Links:
  Alpha -> Beacon
```

To let Beacons see Alpha too:

```text
Visibility Links:
  Alpha <-> Beacon: Two Way
```

Most of the time, use one-way from students to Beacon only if the Beacon should appear on the map but not receive student visibility in return.

## Example 5: Staff See Staff, Students Do Not See Staff

Goal:

- Staff can see each other.
- Staff can see all students.
- Students see only their own teams.
- Students do not see staff.

Create roles:

```text
Staff:
  Can see everyone: On
  Can send everyone: On

Student:
  Can see assigned groups: On
  Can send assigned groups: On
```

Create groups:

```text
Staff
Alpha
Bravo
```

Assign:

```text
Staff users:
  Role: Staff
  Groups: Staff

Alpha students:
  Role: Student
  Groups: Alpha

Bravo students:
  Role: Student
  Groups: Bravo
```

Links:

```text
Staff <-> Alpha: No Link
Staff <-> Bravo: No Link
Alpha <-> Bravo: No Link unless needed
```

Why this works:

- Staff can see everyone because of the Staff role.
- Staff can see other staff because they also share the Staff group.
- Students cannot see Staff because students do not share the Staff group and no student group links to Staff.

## Example 6: Multi-Group User

Goal:

- One user should participate in Alpha and Bravo.

Assign:

```text
Role: Team Member
Groups: Alpha, Bravo
```

With "Can see assigned groups" enabled, that user can see members of both Alpha and Bravo because they share a group with both teams.

Use this for liaison users, floaters, or instructors who should behave like normal team members in multiple groups.

## Common Mistakes

### Mistake: Linking Groups When A Role Is Enough

If an instructor needs to see everyone, give the instructor role "Can see everyone." Do not put instructors in every student group unless students should also see instructors.

### Mistake: Expecting Links To Be Two-Way

`Alpha -> Bravo` is one-way. Use Two Way if both groups should see and send to each other.

### Mistake: Giving Beacon Users Team Member Permissions

If Beacon users have "Can see assigned groups" and share a group with students, they may see students. For isolated behavior, give Beacon users an isolated role.

### Mistake: Forgetting Access Enforcement

If Access Enforcement is off, your policy may look right in the GUI but not be fully applied. Keep Access Enforcement on for real use.

### Mistake: Not Using Access Preview

Always preview at least one user from each group after making changes.

## Recommended Admin Workflow

For a new event:

1. Create roles:
   - Admin or Instructor
   - Team Member or Student
   - Isolated or Beacon if needed
2. Create groups:
   - Alpha
   - Bravo
   - Staff if staff should see each other as a group
   - Beacon if needed
3. Create or bulk create Connection Users.
4. Use Bulk Membership to assign roles and groups.
5. Set Visibility Links.
6. Use Access Preview.
7. Test with two devices before distributing all credentials.

For a live change:

1. Use Bulk Membership to move users or add a temporary group.
2. Use Visibility Links for temporary team merges.
3. Use Access Preview.
4. Refresh connected TAK clients if behavior does not update immediately.

## Troubleshooting Checklist

If a user cannot see another user:

1. Is Access Enforcement on?
2. Is the target user active and connected?
3. Does the viewer have "Can see everyone"?
4. Do both users share a group and does the viewer role have "Can see assigned groups"?
5. Is there a directional link from the viewer's group to the target's group?
6. Does Access Preview show the target under Can See?

If a user cannot send to another user:

1. Does the sender have "Can send everyone"?
2. Do both users share a group and does the sender role have "Can send assigned groups"?
3. Is there a directional link from the sender's group to the receiver's group?
4. Does Access Preview show the receiver under Can Send To?

If a user cannot receive from another user:

1. Does the receiver have "Can receive everyone"?
2. Do both users share a group and does the receiver role have "Can receive assigned groups"?
3. Is there a directional link from the sender's group to the receiver's group?
4. Does Access Preview show the sender under Can Receive From?

If datapackage search or download is confusing:

1. Check whether the package is public or private.
2. Check who created it.
3. Preview whether the requester can see the creator.
4. Preview whether the creator can send to the requester.
5. Preview whether the requester can receive from the creator.
6. Test admin panel package send if needed.

## Field-Test Matrix

Before an event, test one device per policy type.

| Test | Expected Result |
| --- | --- |
| Alpha user previews Alpha user | Can See and Can Send To |
| Alpha user previews Bravo user with no link | Not visible |
| Instructor previews Alpha user | Visible |
| Alpha user previews Instructor | Not visible unless intentionally configured |
| Beacon previews Student | Not visible |
| Instructor previews Beacon | Visible |
| Alpha -> Beacon link enabled | Alpha sees Beacon |
| Alpha <-> Bravo Two Way enabled | Alpha and Bravo see/send/receive both directions |

## Recommended Defaults

For most events:

```text
Access Enforcement: On

Roles:
  Instructor: see everyone, send everyone
  Student: see assigned groups, send assigned groups
  Beacon: no see/send permissions

Groups:
  Alpha
  Bravo
  Beacon if needed
  Staff only if staff should share a staff group

Links:
  No links by default
  Add temporary links only when teams should interact
```

Keep the structure simple. Most deployments only need two or three roles and a handful of groups.
