# FootballData - CLAUDE.md

This file provides guidance to Claude Code when working with the FootballData centralized storage component.

## Component Overview

The **FootballData** directory serves as the centralized data storage for the NFL analytics platform, following the same architecture as BaseballData but adapted for football-specific data structures and weekly scheduling.

## 🔄 CENTRALIZED DATA ARCHITECTURE (NFL VERSION)

**CRITICAL:** FootballData serves as the single source of truth for all NFL data across the multi-sport platform:

- **Single Data Location**: `FootballData/data/` eliminates duplication between FootballTracker, FootballAPI, and FootballScraper
- **Real-time Updates**: Changes appear immediately across all NFL components
- **Weekly Structure**: Organized by season/week instead of daily format
- **Consistent Integration**: All NFL components read from same centralized source

## Directory Structure

### Core Data Organization
```
FootballData/
├── data/                           # Main centralized data directory
│   ├── stats/                      # Player and team statistics
│   │   ├── player_stats.json      # Individual player metrics
│   │   ├── team_stats.json        # Team performance data
│   │   ├── defensive_stats.json   # Defensive unit statistics
│   │   └── nfl_teams.json         # Team information and metadata
│   ├── predictions/                # Generated analysis and predictions
│   │   ├── td_predictions/         # Touchdown probability analysis
│   │   ├── fantasy_projections/    # Fantasy football projections
│   │   └── weekly_analysis/        # Week-by-week analysis files
│   ├── rolling_stats/              # Rolling statistical analysis
│   │   ├── season_stats/           # Full season statistics
│   │   ├── last_4_weeks/           # Recent form analysis
│   │   └── last_2_weeks/           # Short-term trends
│   ├── team_stats/                 # Team-level aggregated data
│   ├── odds/                       # Betting odds and line movement
│   ├── lineups/                    # Starting lineups and depth charts
│   ├── hellraiser/                 # Strategic analysis (NFL version)
│   ├── injuries/                   # Injury reports and status
│   ├── handedness/                 # QB throwing hand preferences
│   ├── stadium/                    # Stadium factors and weather
│   └── multi_td_stats/             # Multi-touchdown game analysis
├── CSV_BACKUPS/                    # Raw CSV files from scraping
└── SCANNED/                        # Processed schedule files
```

## Data Formats and Structure

### Weekly vs Daily Organization
Unlike baseball's daily structure, NFL data is organized by season and week:

**File Naming Convention:**
- `week_01_2025.json` - Week 1 of 2025 season
- `wildcard_2025.json` - Wild card playoff week
- `superbowl_2025.json` - Super Bowl week

**Date Range Handling:**
- Regular Season: Weeks 1-18
- Playoffs: Weeks 19-22 (wildcard, divisional, conference, superbowl)
- Season typically runs September through February

### Player Statistics Schema
```json
{
  "player_001": {
    "name": "Player Name",
    "team": "TEAM",
    "position": "QB|RB|WR|TE|K|DEF",
    "age": 28,
    "season_touchdowns": 12,
    "games_played": 8,
    "snap_percentage": 0.98,
    "target_share": 0.24,           // WR/TE/RB receiving
    "reception_rate": 0.72,         // Catch rate
    "yards_per_target": 9.8,        // Receiving efficiency
    "red_zone_target_share": 0.22,  // Red zone opportunities
    "carries_per_game": 18.5,       // RB rushing
    "yards_per_carry": 5.8,         // Rushing efficiency
    "goal_line_carries": 2.1,       // Goal line opportunities
    "recent_touchdowns": 4,         // Last 3 games
    "recent_games_count": 3,        // Sample size
    "recent_usage_trend": 0.1,      // Increasing/decreasing usage
    "injury_status": "healthy",     // healthy|questionable|doubtful|out
    "recent_trend": "improving",    // improving|stable|declining
    "last_season_td_rate": 1.1      // Year-over-year comparison
  }
}
```

### Team Statistics Schema
```json
{
  "TEAM": {
    "name": "Team Full Name",
    "conference": "AFC|NFC",
    "division": "North|South|East|West",
    "city": "City Name",
    "abbreviation": "TEAM",
    "primary_color": "#HEX",
    "secondary_color": "#HEX",
    "stadium": "Stadium Name",
    "dome": true|false,
    "offensive_stats": {
      "points_per_game": 24.5,
      "yards_per_game": 385.2,
      "passing_yards_per_game": 265.8,
      "rushing_yards_per_game": 119.4,
      "red_zone_efficiency": 0.58,
      "third_down_conversion": 0.42
    },
    "defensive_stats": {
      "points_allowed_per_game": 21.3,
      "yards_allowed_per_game": 342.1,
      "pass_defense_rank": 15,
      "run_defense_rank": 8,
      "turnovers_forced_per_game": 1.2,
      "sacks_per_game": 2.8
    }
  }
}
```

### Defensive Statistics Schema
```json
{
  "TEAM": {
    "team": "Team Full Name",
    "points_per_game": 21.4,           // Points allowed per game
    "yards_allowed_per_game": 331.2,   // Total yards allowed
    "pass_defense_rank": 11,           // League ranking (1-32)
    "run_defense_rank": 10,            // League ranking (1-32)
    "red_zone_td_percentage": 0.54,    // Red zone TD % allowed
    "turnovers_per_game": 1.4,         // Turnovers forced per game
    "sacks_per_game": 2.8,             // Sacks per game
    "interceptions_per_game": 0.6,     // Interceptions per game
    "fumbles_recovered_per_game": 0.8  // Fumbles recovered per game
  }
}
```

## Integration Points

### FootballScraper Integration
- **CSV Output**: All scraped data outputs to `FootballData/CSV_BACKUPS/`
- **Processing**: Raw CSV files processed into JSON format in `data/stats/`
- **Schedule Files**: Weekly schedule files stored in `SCANNED/`
- **Game Data**: Individual game statistics extracted and centralized

### FootballTracker Integration
- **Data Source**: Reads all data from `../FootballData/data/`
- **Proxy Configuration**: Development proxy serves `/data/` from centralized location
- **Production Build**: Symlink `build/data` → `../../FootballData/data`
- **Real-time Updates**: Changes appear immediately without rebuilds

### FootballAPI Integration
- **Analysis Engine**: Reads player and defensive stats for six-component scoring
- **Predictions**: Outputs TD predictions and fantasy projections to centralized location
- **Confidence Scoring**: Uses data completeness from centralized storage
- **Fallback System**: League averages stored centrally for missing data scenarios

## Data Processing Pipeline

### Weekly Data Collection
```bash
# 1. FootballScraper collects weekly game data
cd FootballScraper
python enhanced_nfl_scrape.py --week 1 --season 2025
# Outputs: CSV files to ../FootballData/CSV_BACKUPS/

# 2. Process and convert to JSON format
node src/services/processNFLStats.js --week 1 --season 2025
# Outputs: JSON files to ../FootballData/data/stats/

# 3. Generate predictions and analysis
cd ../FootballAPI
python enhanced_main.py
# Reads: ../FootballData/data/stats/
# Outputs: ../FootballData/data/predictions/

# 4. Update frontend with fresh data
cd ../FootballTracker
npm start
# Serves: ../FootballData/data/ via proxy
```

### Data Quality and Validation
- **Completeness Checking**: Validate required fields for confidence scoring
- **Schema Validation**: Ensure all JSON files match expected structure
- **Cross-Reference Validation**: Verify player-team assignments and statistics
- **Historical Consistency**: Check for major statistical anomalies

## NFL-Specific Considerations

### Positional Categories
- **Skill Positions**: QB, RB, WR, TE (primary fantasy relevance)
- **Offensive Line**: LT, LG, C, RG, RT (blocking analysis)
- **Defense**: DE, DT, LB, CB, S (defensive matchup analysis)
- **Special Teams**: K, P, LS (kicking game analysis)

### Scoring Systems
- **Touchdown Scoring**: Six-component system adapted for NFL
- **Fantasy Projections**: Standard, PPR, and Half-PPR formats
- **Confidence Levels**: Data quality assessment for reliability
- **Matchup Analysis**: Position-specific defensive matchup evaluation

### Schedule Considerations
- **Bye Weeks**: Players not available during team bye weeks
- **Thursday/Monday Games**: Short rest impact on performance
- **International Games**: Travel and time zone considerations
- **Weather Impact**: Outdoor vs dome games, temperature, wind, precipitation

## Performance Optimization

### Caching Strategy
- **Player Statistics**: Cache for 24 hours during season
- **Team Statistics**: Cache for 1 week (updated after each game week)
- **Predictions**: Generate fresh for each analysis request
- **Historical Data**: Long-term cache for season-over-season comparisons

### Data Loading Patterns
- **Lazy Loading**: Load only required week/season data
- **Batch Processing**: Process multiple weeks efficiently
- **Parallel Processing**: Handle multiple position groups simultaneously
- **Memory Management**: Clear outdated data automatically

## Error Handling and Fallbacks

### Missing Data Scenarios
- **Player Injuries**: Use injury status to adjust expectations
- **Limited Sample Size**: Fall back to position averages
- **New Players**: Use college statistics or rookie projections
- **Team Changes**: Handle trades and roster moves

### Data Quality Issues
- **Incomplete Statistics**: Flag low-confidence predictions
- **Conflicting Sources**: Prioritize official NFL data
- **Delayed Updates**: Show last updated timestamps
- **Validation Failures**: Log errors and use fallback data

## Future Enhancements

### Planned Features
- **Advanced Metrics**: EPA, DVOA, PFF grades integration
- **Injury Impact Analysis**: Quantify injury status on performance
- **Weather Integration**: Real-time weather data for outdoor games
- **Betting Line Integration**: Odds movement and value analysis

### Scalability Considerations
- **Multi-Season Support**: Historical data across multiple seasons
- **Real-time Updates**: Live game data integration
- **Advanced Analytics**: Machine learning model integration
- **API Rate Limiting**: Manage external data source limitations

## Dependencies

### Data Sources
- **ESPN NFL**: Game statistics and box scores
- **NFL Official Data**: Roster and injury information
- **Weather Services**: Outdoor game conditions
- **Betting Odds**: Line movement and public betting data

### System Requirements
- **Storage**: Approximately 500MB per season
- **Processing**: Node.js for JSON processing, Python for analysis
- **Memory**: 2GB recommended for full season analysis
- **Network**: Reliable internet for data scraping and updates

This centralized architecture ensures consistent, real-time data access across all NFL analytics components while maintaining the same reliability and performance as the proven baseball system.