# Farm Management System (FMS) Web App

## Design Decisions

The FMS web app is structured using Flask with routes that handle interactions for paddocks, mobs, and stock management. Here are the key design decisions made:

- **Routing & Page Interaction**: Each feature, such as viewing paddocks, advancing the current date, and moving mobs, has its own dedicated route (`/paddocks`, `/advance_date`, `/move_mob`). This keeps each page focused on a specific function, enhancing clarity and maintainability.
  
- **POST vs. GET**: POST is used for actions that modify the database or application state, such as adding a paddock or moving a mob. This ensures that users do not accidentally repeat actions by refreshing the page. GET is used for retrieving data to be displayed, such as when viewing paddocks or mobs.
  
- **Template Rendering**: Each page h as its own HTML template, such as `paddocks.html`, `move_mob.html`, etc., to maintain separation of concerns. However, forms for editing and adding entities (like paddocks) use similar layouts to ensure consistency.
  
- **Pasture Growth and Stock Consumption**: The app automatically updates pasture data based on the daily growth rate (65 kg DM/ha/day) and consumption rate (14 kg DM/animal/day). This is recalculated each time the date advances. The app ensures that mobs and paddocks stay within the logical constraints, preventing one paddock from hosting multiple mobs.

- **Database Connection**: To manage the connection efficiently, a helper function `getCursor()` is used to get or create a new database connection if necessary. This reduces redundancy and ensures that the app can handle the database efficiently.

- **Session Management**: The session stores the current date to track progress across user interactions. This ensures that users are always working with the latest simulation data, and any actions that depend on the current date (e.g., advancing it) work consistently.

## Image Sources

This project currently does not use any external images.

## Database Questions

1. **What SQL statement creates the mobs table and defines its fields/columns?**

    ```sql
    CREATE TABLE mobs (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) DEFAULT NULL,
    paddock_id INT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX paddock_idx (paddock_id),
    CONSTRAINT fk_paddock FOREIGN KEY (paddock_id)
        REFERENCES paddocks (id)
        ON DELETE NO ACTION ON UPDATE NO ACTION
    );
    ```

2. **Which lines of SQL script set up the relationship between the mobs and paddocks tables?**

    The foreign key relationship between the `mobs` and `paddocks` tables is established with the following line:
    
    ```sql
     CONSTRAINT fk_paddock FOREIGN KEY (paddock_id)
        REFERENCES paddocks (id)
    ```

3. **SQL script to create a new table called farms:**

    ```sql
    CREATE TABLE farms (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        owner_name VARCHAR(255) NOT NULL
    );
    ```

4. **SQL statement to add details for an example farm:**

    ```sql
    INSERT INTO farms (name, description, owner_name)
    VALUES ('Green Meadows', 'A small organic farm specializing in pasture-raised livestock', 'John Doe');
    ```

5. **What changes would you need to make to other tables to incorporate the new farms table?**

    To incorporate the new `farms` table, the following changes would be needed:
    
    - Add a `farm_id` column to the `paddocks`, `mobs`, and `stock` tables to associate them with a farm.
    - Update the existing queries to filter by `farm_id` where appropriate, ensuring that each paddock, mob, or stock belongs to a specific farm.
    - Modify forms and routes to include the selection or assignment of farms when adding or editing paddocks, mobs, or stock.

## Model Notes

The relationship between the tables is as follows:
- `mobs.paddock_id` refers to `paddocks.id`
- `stock.mob_id` refers to `mobs.id`

Each table has its respective foreign key, ensuring the hierarchical structure and relationships between paddocks, mobs, and stock are maintained.
