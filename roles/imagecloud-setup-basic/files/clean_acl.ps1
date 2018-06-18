$acl = Get-Acl E:\
$acl.SetAccessRuleProtection($false,$false)
$acl.Access | %{$acl.RemoveAccessRule($_)}
set-Acl E:\ $acl
