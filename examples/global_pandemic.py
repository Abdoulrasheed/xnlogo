"""Global pandemic epidemic model - NetLogo translation."""

from xnlogo import agent
from xnlogo.runtime.ui import Button, Switch, Monitor, Plot, PlotPen, View, Interface


@agent
class GlobalModel:
    """Global configuration and statistics (maps to NetLogo globals)."""
    
    student_id: str = ""
    student_name: str = ""
    student_score: int = 0
    student_feedback: str = ""
    
    most_effective_measure: int = 0
    least_effective_measure: int = 0
    population_with_highest_mortality_rate: int = 0
    population_most_immune: int = 0
    self_isolation_link: int = 0
    population_density: int = 0
    
    total_infected_percentage: float = 0.0
    turquoise_infected_percentage: float = 0.0
    magenta_infected_percentage: float = 0.0
    
    total_deaths: int = 0
    turquoise_deaths: int = 0
    magenta_deaths: int = 0
    
    total_antibodies_percentage: float = 0.0
    turquoise_antibodies_percentage: float = 0.0
    magenta_antibodies_percentage: float = 0.0
    
    stored_settings: str = ""
    
    turquoise_population: int = 250
    magenta_population: int = 1000
    initially_infected: int = 25
    infection_rate: int = 35
    survival_rate: int = 40
    immunity_duration: int = 160
    undetected_period: int = 175
    illness_duration: int = 390
    
    travel_restrictions: bool = False
    social_distancing: bool = False
    self_isolation: bool = False
    
    def setup_world(self):
        """Initialize the world and global variables."""
        pass
    
    def setup_agents(self):
        """Create initial populations and infect some agents."""
        pass
    
    def run_model(self):
        """Main simulation step."""
        pass
    
    def split_world(self):
        """Divide world into turquoise and magenta halves."""
        pass
    
    def sprout_agent_population(self):
        """Helper to spawn agent populations."""
        pass
    
    def update_stats(self):
        """Calculate and update all statistics."""
        pass
    
    def my_analysis(self):
        """Record analysis results."""
        pass


@agent
class Person:
    """Individual agent in the pandemic simulation."""
    
    infected_time: int = 0
    antibodies: int = 0
    group: str = ""
    isolating: bool = False
    
    def check_travel_restrictions(self):
        """Enforce movement restrictions between regions."""
        pass
    
    def check_social_distancing(self):
        """Implement social distancing movement."""
        pass
    
    def check_self_isolation(self):
        """Handle infection, isolation, recovery, and death."""
        pass


interface = Interface(
    view=View(765, 0, 510, 510, patch_size=5.0, frame_rate=20.0),
    buttons=[
        Button(15, 555, 355, 40, "setup_world"),
        Button(15, 605, 355, 40, "setup_agents"),
        Button(15, 655, 355, 40, "run_model", forever=True),
    ],
    switches=[
        Switch(15, 705, 355, 40, "travel_restrictions"),
        Switch(15, 755, 355, 40, "social_distancing"),
        Switch(15, 805, 355, 40, "self_isolation"),
    ],
    plots=[
        Plot(
            10,
            10,
            750,
            225,
            "Population",
            x_axis="Hours",
            y_axis="Number of People",
            pens=[
                PlotPen(
                    "Infected",
                    color="orange",
                    update="plot count turtles with [infected_time > 0]",
                ),
                PlotPen(
                    "Immune",
                    color="brown",
                    update="plot count turtles with [antibodies > 0]",
                ),
            ],
        ),
        Plot(
            10,
            240,
            335,
            260,
            "Populations",
            x_axis="Population",
            y_axis="Time",
            pens=[
                PlotPen(
                    "Magenta Population",
                    color="red",
                    update='plot count turtles with [group = "magenta turtle"]',
                ),
                PlotPen(
                    "Torquoise Population",
                    color="black",
                    update='plot count turtles with [group = "turquoise turtle"]',
                ),
                PlotPen(
                    "Magenta Population",
                    color="red",
                    update='plot count turtles with [group = "magenta turtle"]',
                ),
            ],
        ),
    ],
    monitors=[
        Monitor(x=380, y=240, width=165, height=60, variable="total_infected_percentage"),
        Monitor(x=550, y=240, width=210, height=60, variable="turquoise_antibodies_percentage"),
        Monitor(x=535, y=305, width=100, height=60, variable="total_deaths"),
        Monitor(x=415, y=305, width=115, height=60, variable="magenta_deaths"),
        Monitor(x=640, y=305, width=120, height=60, variable="turquoise_deaths"),
        Monitor(x=365, y=370, width=185, height=60, variable="total_antibodies_percentage"),
        Monitor(x=555, y=370, width=210, height=60, variable="turquoise_infected_percentage"),
        Monitor(x=350, y=435, width=200, height=60, variable="magenta_infected_percentage"),
        Monitor(
            x=555,
            y=435,
            width=100,
            height=60,
            expression="count turtles with [antibodies > 0]",
            label="Active Cases",
        ),
        Monitor(x=660, y=435, width=100, height=60, variable="count turtles"),
        Monitor(x=545, y=500, width=215, height=60, variable="magenta_antibodies_percentage"),
    ],
)
