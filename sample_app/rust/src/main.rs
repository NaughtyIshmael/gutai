mod calculator;
mod task_manager;
mod utils;

use calculator::Calculator;
use task_manager::TaskManager;
use utils::format_output;

fn main() {
    let calc = Calculator::new();
    let result = calc.add(10.0, 5.0);
    println!("{}", format_output("Addition result", &result.to_string()));

    let mut task_manager = TaskManager::new();
    task_manager.add_task("Sample task".to_string());
    println!(
        "{}",
        format_output("Task count", &task_manager.task_count().to_string())
    );
}
