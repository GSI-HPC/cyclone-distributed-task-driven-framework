# Lustre OST Migration

Migrate files on Lustre between OSTs.  

The file migration is done from source to target OSTs until a specific fill threshold is reached.  

To keep the load of the Lustre OSS low, the file migration does a 1-to-1 mapping between source to target OSTs.  

If more than one source and target OST should be used to increase the file migration processes at a time,  
this feature must be implemented (see [issue](https://github.com/GSI-HPC/cyclone-distributed-task-driven-framework/issues/27)).  

To migrate files on Lustre OSTs Cyclone uses so called input files.  
An input file consists of datasets with two columns separated with a whitespace for each file to migrate:  
1. Decimal OST index
2. Filepath

> The OST indexes within input files define the source OST indexes that Cyclone will migrate data from.  
> Therefore it is not required to specify those indexes, since Cyclone will determine them automatically.

To speed up a migration, Robinhood is used to determine the OST index where a file is located on Lustre.  
Please refer to the following [slides](../Slides/2024_02_22-lustre_file_migration.pdf) for a Lustre file migration.  

As for the task result description please refer to the [lfs-utils library MigrateResult class](https://github.com/GSI-HPC/lfs-utils). 

## Configuration

### [Task Generator](../task/generator/lustre_ost_migration_task_generator.py)

[Example config file for the task generator](../Configuration/lustre_ost_migration_task_generator.conf)

#### Section: control

| Name        | Type   | Value                              | Description                                      |
| ----------- | ------ | ---------------------------------- | ------------------------------------------------ |
| local\_mode | String | yes/no, on/off, true/false and 1/0 | Specifies if local or productive mode is enabled |

#### Section: control.local\_mode

| Name        | Type   | Value  | Description                                     |
| ----------- | ------ | ------ | ----------------------------------------------- |
| num\_osts   | Int    | 1-1000 | Specifies the number of Lustre OSTs to simulate |

#### Section: control.threshold

| Name                | Type   | Value  | Description                                                              |
| ------------------- | ------ | ------ | ------------------------------------------------------------------------ |
| update\_fill\_level | Int    | 1-3600 | Time in seconds when to update Lustre OSTs fill level                    |
| reload\_files       | Int    | 1-3600 | Time in seconds when to reload input files                               |
| print\_caches       | Int    | 1-3600 | Time in seconds when to print the caches with number of files to migrate |

#### Section: task

| Name       | Type   | Value | Description              |
| ---------- | ------ | ----- | ------------------------ |
| task\_file | String | Path  | Path to task config file |
| task\_name | String | Name  | Name of task to load     |

#### Section: migration

| Name                         | Type     | Value | Description                                                                 |
| ---------------------------- | -------- | ----- | --------------------------------------------------------------------------- |
| input\_dir                   | String   | Path  | Path to input directory where to process input file lists from              |
| ost\_fill\_threshold\_source | Int      | 0-90  | Lustre OST fill level threshold in percentage for reducing down source OSTs |
| ost\_fill\_threshold\_target | Int      | 1-90  | Lustre OST fill level threshold in percentage for filling up target OSTs    |
| ost\_targets                 | RangeSet | n>=0  | List of decimal OST indexes comma separated and ranges defined with hyphen  |

#### Section: lustre

| Name      | Type   | Value  | Description            |
| --------- | ------ | ------ | ---------------------- |
| fs\_path  | String | Path   | Lustre filesystem path |

### [Task](../task/lustre_ost_migrate_task.py)

[Example config file for the task](../Configuration/lustre_ost_migration_tasks.xml)

| Name        | Type   | Value      | Description                        |
| ----------- | ------ | ---------- | ---------------------------------- |
| filename    | String | -          | Placeholder, filled during runtime |
| source\_ost | Int    | -          | Placeholder, filled during runtime |
| target\_ost | Int    | -          | Placeholder, filled during runtime |
| direct\_io  | Bool   | True/False | Enables direct IO                  |
| block       | Bool   | True/False | Enables blocking file migration    |
| skip        | Bool   | True/False | Skip stripped files                |

