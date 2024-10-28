def update_grid(grid):
    new_grid = [[HOUSE for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == HOUSE:
                # Check for adjacent houses
                adjacent_houses = 0
                if i > 0 and grid[i - 1][j] == HOUSE:  # Up
                    adjacent_houses += 1
                if i < GRID_SIZE - 1 and grid[i + 1][j] == HOUSE:  # Down
                    adjacent_houses += 1
                if j > 0 and grid[i][j - 1] == HOUSE:  # Left
                    adjacent_houses += 1
                if j < GRID_SIZE - 1 and grid[i][j + 1] == HOUSE:  # Right
                    adjacent_houses += 1
                
                # If there are 2 adjacent houses, turn one into a skyscraper
                if adjacent_houses == 2:
                    new_grid[i][j] = SKYSCRAPER
                else:
                    new_grid[i][j] = HOUSE
            else:
                new_grid[i][j] = SKYSCRAPER  # Keep existing skyscrapers
    return new_grid




# Function to determine the next state based on the current grid
def update_grid(grid):
    new_grid = grid.copy()

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = grid[i][j]
            
            # Get neighboring cells
            neighbors = [grid[x][y] for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                                    for y in range(max(0, j-1), min(GRID_SIZE, j+2)) 
                                    if (x, y) != (i, j)]
            
            # Rule: If the cell is empty and near a road, it might turn into a house
            if current_state == EMPTY:
                if ROAD in neighbors:
                    new_grid[i][j] = HOUSE
            
            # Rule: Houses surrounded by many houses upgrade to skyscrapers
            elif current_state == HOUSE:
                if neighbors.count(HOUSE) > 4:
                    new_grid[i][j] = SKYSCRAPER
            
            # Rule: Skyscrapers near too many parks might downgrade to houses
            elif current_state == SKYSCRAPER:
                if neighbors.count(PARK) > 2:
                    new_grid[i][j] = HOUSE
            
            # Rule: Parks remain parks
            elif current_state == PARK:
                if neighbors.count(EMPTY) > 5:
                    new_grid[i][j] = PARK  # Parks remain unchanged

    return new_grid