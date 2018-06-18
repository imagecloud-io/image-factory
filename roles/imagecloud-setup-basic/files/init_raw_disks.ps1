Write-Host "Initializing and formatting raw disks"

  #Change CD drive letter
  $drv = Get-WmiObject win32_volume -filter 'DriveType = 5'
  $drv.DriveLetter = "X:"
  $drv.Put() | out-null

  $disks = Get-Disk | where partitionstyle -eq 'raw'

  ## start at E: because D: is reserved in Azure. Exclude X because we just assigned that one to the CD drive.
  $letters = New-Object System.Collections.ArrayList
  $letters.AddRange( ('E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','Y','Z') )

  Function AvailableVolumes() {
      $currentDrives = get-volume
      ForEach ($v in $currentDrives) {
          if ($v.DriveLetter -and ($letters -contains $v.DriveLetter.ToString())) {
              Write-Host "Drive letter $($v.DriveLetter) is taken, moving to next letter"
              $letters.Remove($v.DriveLetter.ToString())
          }
      }
  }

  ForEach ($d in $disks) {
      AvailableVolumes
      $driveLetter = $letters[0]
      Write-Host "Creating volume $($driveLetter)"
      $d | Initialize-Disk -PartitionStyle MBR -PassThru | New-Partition -DriveLetter $driveLetter  -UseMaximumSize
      # Prevent error ' Cannot perform the requested operation while the drive is read only'
      Start-Sleep 1
      Format-Volume  -FileSystem NTFS -NewFileSystemLabel "datadisk" -DriveLetter $driveLetter -Confirm:$false
  }

