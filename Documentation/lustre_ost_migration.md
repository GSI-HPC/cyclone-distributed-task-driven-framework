# Lustre OST Migration

Migrate files on Lustre between OSTs.

## Description

## Configuration

[Configuration File for Task Generator](../Configuration/lustre_ost_migration_task_generator.conf)

### Section: **control**

| Name        | Type   | Value                              | Description                                      |
| ----------- | ------ | ---------------------------------- | ------------------------------------------------ |
| local\_mode | String | yes/no, on/off, true/false and 1/0 | Specifies if local or productive mode is enabled |

### Section: **control.local_mode**

| Name        | Type   | Value  | Description                                     |
| ----------- | ------ | ------ | ----------------------------------------------- |
| num\_osts   | Number | 1-1000 | Specifies the number of Lustre OSTs to simulate |

### Section: **control.threshold**

| Name                | Type   | Value  | Description                                                                     |
| ------------------- | ------ | ------ | ------------------------------------------------------------------------------- |
| update\_fill\_level | Number | 1-3600 | Time period in seconds when to update Lustre OSTs fill level                    |
| reload\_files       | Number | 1-3600 | Time period in seconds when to reload input files                               |
| print\_caches       | Number | 1-3600 | Time period in seconds when to print the caches with number of files to migrate |

### Section: **task**

| Name       | Type   | Value  | Description           |
| ---------- | ------ | ------ | --------------------- |
| task\_file | String | Path   | Path to task XML file |
| task\_name | String | Path   | Name of task to load  |

### Section: **migration**

| Name                         | Type     | Value | Description                                                                 |
| ---------------------------- | -------- | ----- | --------------------------------------------------------------------------- |
| input\_dir                   | String   | Path  | Path to input directory where to process input file lists from              |
| ost\_fill\_threshold\_source | Number   | 0-90  | Lustre OST fill level threshold in percentage for reducing down source OSTs |
| ost\_fill\_threshold\_target | Number   | 1-90  | Lustre OST fill level threshold in percentage for filling up target OSTs    |
| ost\_targets                 | RangeSet | 0-999 | List of decimal OST indexes comma separated and ranges defined with hyphen  |

### Section: **lustre**

| Name      | Type   | Value  | Description            |
| --------- | ------ | ------ | ---------------------- |
| fs\_path  | String | Path   | Lustre filesystem path |

## Input File Lists

The input file lists to be processed must be located within the directory specified in the `input_dir` parameter  
of the task generators config file:

```
[migration]
input_dir = ...
```
