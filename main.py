from config import STATIC_SIMULATION_CONFIG
from simulation.static_simulation import SimulationRunner

def main():
    """
    Main function to execute the simulation and save the results.
    """
    # 1. Initialize the runner with the configuration
    runner = SimulationRunner(config=STATIC_SIMULATION_CONFIG)
    
    # 2. Run the simulation to get the results DataFrame
    results_dataframe = runner.run()
    
    # 3. Save the results to a file for later use
    output_file = STATIC_SIMULATION_CONFIG['results_filename']
    results_dataframe.to_csv(output_file, index=False)
    print(f"\n💾 Results successfully saved to '{output_file}'")

if __name__ == '__main__':
    main()
