{{- define "lp.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end -}}
