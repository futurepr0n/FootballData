#!/usr/bin/env python3
"""
Test Complete Football Data Pipeline
Validates end-to-end functionality from data to dashboard
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoints():
    """Test all API endpoints"""
    endpoints = [
        ("health", "http://localhost:9000/health"),
        ("recent games", "http://localhost:9000/api/games/recent?limit=5"),
        ("passing leaders", "http://localhost:9000/api/leaderboards/passing?limit=5"),
        ("rushing leaders", "http://localhost:9000/api/leaderboards/rushing?limit=5"),
        ("receiving leaders", "http://localhost:9000/api/leaderboards/receiving?limit=5"),
        ("interceptions", "http://localhost:9000/api/leaderboards/interceptions?limit=5"),
        ("stats summary", "http://localhost:9000/api/stats/summary"),
    ]
    
    results = {}
    
    print("🔌 Testing API Endpoints")
    print("=" * 40)
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Extract key metrics
                if name == "health":
                    metrics = f"Status: {data.get('status', 'unknown')}, Files: {data.get('data_files_available', 0)}"
                elif name == "recent games":
                    games_count = len(data.get('games', []))
                    metrics = f"{games_count} games"
                elif "leaders" in name:
                    leaders_count = len(data.get('leaders', []))
                    top_player = data.get('leaders', [{}])[0].get('name', 'No data') if data.get('leaders') else 'No data'
                    metrics = f"{leaders_count} players, Top: {top_player}"
                elif name == "stats summary":
                    total_games = data.get('total_games', 0)
                    total_weeks = data.get('total_weeks', 0)
                    metrics = f"{total_games} games across {total_weeks} weeks"
                else:
                    metrics = f"OK ({len(str(data))} chars)"
                
                print(f"✅ {name:<20}: {metrics}")
                results[name] = "success"
                
            else:
                print(f"❌ {name:<20}: HTTP {response.status_code}")
                results[name] = f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"❌ {name:<20}: {str(e)[:50]}")
            results[name] = f"Error: {str(e)[:30]}"
    
    return results

def test_dashboard_connectivity():
    """Test FootballTracker dashboard"""
    print(f"\n🖥️  Testing Dashboard Connectivity")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:4000", timeout=5)
        if response.status_code == 200:
            if "NFL Stat Tracker" in response.text:
                print("✅ FootballTracker: Dashboard accessible")
                return True
            else:
                print("⚠️  FootballTracker: Accessible but unexpected content")
                return False
        else:
            print(f"❌ FootballTracker: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FootballTracker: {e}")
        return False

def test_data_quality():
    """Test data quality and completeness"""
    print(f"\n📊 Testing Data Quality")
    print("=" * 40)
    
    quality_checks = []
    
    try:
        # Test rushing leaders quality
        response = requests.get("http://localhost:9000/api/leaderboards/rushing?limit=10", timeout=5)
        rushing_data = response.json()
        
        rushing_leaders = rushing_data.get('leaders', [])
        if rushing_leaders:
            has_yards = any(p.get('yards', 0) > 0 for p in rushing_leaders)
            has_touchdowns = any(p.get('touchdowns', 0) > 0 for p in rushing_leaders)
            has_names = all(p.get('name') for p in rushing_leaders)
            
            print(f"✅ Rushing Leaders: {len(rushing_leaders)} players")
            print(f"   - Has yards data: {has_yards}")
            print(f"   - Has touchdown data: {has_touchdowns}")
            print(f"   - All have names: {has_names}")
            
            quality_checks.append(len(rushing_leaders) > 0 and has_names)
        else:
            print("⚠️  Rushing Leaders: No data")
            quality_checks.append(False)
        
        # Test receiving leaders quality  
        response = requests.get("http://localhost:9000/api/leaderboards/receiving?limit=10", timeout=5)
        receiving_data = response.json()
        
        receiving_leaders = receiving_data.get('leaders', [])
        if receiving_leaders:
            has_yards = any(p.get('yards', 0) > 0 for p in receiving_leaders)
            has_touchdowns = any(p.get('touchdowns', 0) > 0 for p in receiving_leaders)
            has_names = all(p.get('name') for p in receiving_leaders)
            
            print(f"✅ Receiving Leaders: {len(receiving_leaders)} players")
            print(f"   - Has yards data: {has_yards}")
            print(f"   - Has touchdown data: {has_touchdowns}")
            print(f"   - All have names: {has_names}")
            
            quality_checks.append(len(receiving_leaders) > 0 and has_names)
        else:
            print("⚠️  Receiving Leaders: No data")
            quality_checks.append(False)
        
        # Test interceptions quality
        response = requests.get("http://localhost:9000/api/leaderboards/interceptions?limit=10", timeout=5)
        int_data = response.json()
        
        int_leaders = int_data.get('leaders', [])
        if int_leaders:
            has_interceptions = all(p.get('interceptions', 0) > 0 for p in int_leaders)
            has_names = all(p.get('name') for p in int_leaders)
            
            print(f"✅ Interception Leaders: {len(int_leaders)} players")
            print(f"   - All have interceptions: {has_interceptions}")
            print(f"   - All have names: {has_names}")
            
            quality_checks.append(len(int_leaders) > 0 and has_names)
        else:
            print("⚠️  Interception Leaders: No data")
            quality_checks.append(False)
            
        # Test games quality
        response = requests.get("http://localhost:9000/api/games/recent?limit=10", timeout=5)
        games_data = response.json()
        
        games = games_data.get('games', [])
        if games:
            has_teams = all(g.get('home_team') and g.get('away_team') for g in games)
            has_scores = any(g.get('home_team', {}).get('score', 0) > 0 for g in games)
            
            print(f"✅ Recent Games: {len(games)} games")
            print(f"   - All have teams: {has_teams}")
            print(f"   - Some have scores: {has_scores}")
            
            quality_checks.append(len(games) > 0 and has_teams)
        else:
            print("⚠️  Recent Games: No data")
            quality_checks.append(False)
            
    except Exception as e:
        print(f"❌ Data Quality Test Failed: {e}")
        quality_checks.append(False)
    
    return quality_checks

def main():
    """Run complete pipeline test"""
    print("🏈 Complete Football Data Pipeline Test")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API endpoints
    api_results = test_api_endpoints()
    
    # Test dashboard
    dashboard_ok = test_dashboard_connectivity()
    
    # Test data quality
    quality_checks = test_data_quality()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 50)
    
    api_success = sum(1 for result in api_results.values() if result == "success")
    api_total = len(api_results)
    
    quality_success = sum(quality_checks)
    quality_total = len(quality_checks)
    
    print(f"API Endpoints: {api_success}/{api_total} passed")
    print(f"Dashboard: {'✅ OK' if dashboard_ok else '❌ Failed'}")
    print(f"Data Quality: {quality_success}/{quality_total} passed")
    
    overall_success = (
        api_success >= api_total * 0.8 and  # 80% of API endpoints working
        dashboard_ok and                     # Dashboard accessible
        quality_success >= quality_total * 0.7  # 70% of data quality checks passing
    )
    
    if overall_success:
        print(f"\n🎉 OVERALL: SUCCESS - Pipeline is operational!")
        print(f"   • Dashboard components should show updated data")
        print(f"   • All major endpoints are functional")
        print(f"   • Data quality is acceptable")
    else:
        print(f"\n⚠️  OVERALL: ISSUES DETECTED")
        if api_success < api_total * 0.8:
            print(f"   • API endpoints need attention ({api_success}/{api_total})")
        if not dashboard_ok:
            print(f"   • Dashboard connectivity issues")
        if quality_success < quality_total * 0.7:
            print(f"   • Data quality issues ({quality_success}/{quality_total})")
    
    print(f"\n🔗 Dashboard URL: http://localhost:4000")
    print(f"🔗 API Health: http://localhost:9000/health")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)