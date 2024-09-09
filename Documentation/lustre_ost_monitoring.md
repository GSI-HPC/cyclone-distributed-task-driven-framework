# Lustre OST Monitoring

The Lustre OST monitoring can detect if Lustre OSTs are showing very low performance  
and thus can be considered as not beeing reactive anymore.  

Since the monitoring task itself does active IO on the OSTs it is recommended to use small amount of test data  
to keep the impact on the production system as low as possible. Tests should also run not to often e.g. once a day.  

The monitoring task results are saved into a MySQL database, but it would be also feasible to save those metrics  
via the Pushgateway client into the Prometheus monitoring system.

## Configuration

### [Monitoring Task Generator](../task/generator/lustre_ost_monitoring_task_generator.py)

[Example config file for the task generator](../Configuration/lustre_ost_monitoring_task_generator.conf)

#### Section: control

| Name                 | Type   | Value                              | Description                                      |
| -------------------- | ------ | ---------------------------------- | ------------------------------------------------ |
| local\_mode          | String | yes/no, on/off, true/false and 1/0 | Specifies if local or productive mode is enabled |
| measure\_interval    | Int    | n>=0                               | Specifies the task creation time in seconds      |

#### Section: task

| Name                 | Type   | Value | Description              |
| -------------------- | ------ | ----- | ------------------------ |
| task\_file           | String | Path  | Path to task config file |
| task\_name           | String | Name  | Name of task to load     |

#### Section: lustre

| Name              | Type     | Value | Description                                                                                                     |
| ------------------| -------- | ------| --------------------------------------------------------------------------------------------------------------- |
| lfs\_bin          | String   | Path  | Path to Lustre lfs binary                                                                                       |
| target            | String   | Name  | Target name of Lustre filessytem                                                                                |
| ost\_select\_list | RangeSet | 0>=n  | List of decimal OST indexes comma separated and ranges defined with hyphen. Leave empty for all available OSTs. |

### [Task](../task/lustre_io_task.py)

[Example config file for the task](../Configuration/lustre_ost_monitoring_tasks.xml)

| Name                         | Type   | Value  | Description                                                        |
| ---------------------------- | -----  | ------ | ------------------------------------------------------------------ |
| ost\_idx                     | Int    | -      | Placeholder, filled during runtime                                 |
| block\_size\_bytes           | Int    | n>0    | Block size in bytes for test data                                  |
| total\_size\_bytes           | Int    | n>0    | Total size in bytes for test data                                  |
| write\_file\_sync            | Bool   | on/off | Sets file sync for writing test                                    |
| target\_dir                  | String | Path   | Path of target directory for test data on Lustre                   |
| lfs\_bin                     | String | Path   | Path to Lustre lfs binary                                          |
| lfs\_target                  | String | Name   | Target name of Lustre filessytem                                   |
| db\_proxy\_target            | String | Host   | Host name of database proxy target                                 |
| db\_proxy\_port              | Int    | Port   | Port of database proxy target                                      |

### [Task](../task/lustre_alert_io_task.py)

[Example config file for the task](../Configuration/lustre_ost_monitoring_tasks.xml)

This task inherits all parameter from the [LustreIOTask](../task/lustre_io_task.py]), but adds alerting.  

| Name                         | Type     | Value | Description                                                                         |
| ---------------------------- | ------   | ----- | ----------------------------------------------------------------------------------- |
| mail\_server                 | String   | Host  | Specifies the mail servers host name                                                |
| mail\_sender                 | String   | Email | Sender email address                                                                |
| mail\_receiver               | String   | Email | Receiver email address                                                              |
| mail\_threshold              | Int      | n>0   | Threshold in seconds for sending an email when OST performance degradation detected |

