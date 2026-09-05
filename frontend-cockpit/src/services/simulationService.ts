import { SimulationResult } from '../types';

export const simulationService = {
  simulateWhatIf: async (blockId: string, newEndTime: string): Promise<SimulationResult> => {
    // Mock simulation behavior based on time extension
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          total_passenger_delay_minutes: 37 + Math.floor(Math.random() * 20),
          regulated_freight_trains: 3 + Math.floor(Math.random() * 2),
          punctuality_impact_pct: -8.4 - (Math.random() * 2),
          conflict_warnings: [
            '⚠ Express 12303 may encounter restriction',
            '⚠ Freight 56821 held at BDC',
            '⚠ Headway conflict predicted near BWN'
          ]
        });
      }, 800);
    });
  }
};
