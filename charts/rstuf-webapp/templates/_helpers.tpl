{{/*
Expand the name of the chart.
*/}}
{{- define "rstuf-webapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "rstuf-webapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "rstuf-webapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "rstuf-webapp.labels" -}}
helm.sh/chart: {{ include "rstuf-webapp.chart" . }}
{{ include "rstuf-webapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "rstuf-webapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "rstuf-webapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "rstuf-webapp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "rstuf-webapp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Add extra annotations to every resource
*/}}
{{- define "rstuf-webapp.annotations" -}}
{{- with .Values.extraAnnotations }}
{{- range $annotation, $value := index . }}
{{ $annotation }}: {{ tpl $value $ | quote }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Name of the Secret holding the trust anchor, whether this chart created it or
the operator brought their own.
*/}}
{{- define "rstuf-webapp.trustedRootSecret" -}}
{{- if .Values.trustedRoot.existingSecret }}
{{- .Values.trustedRoot.existingSecret }}
{{- else }}
{{- printf "%s-trusted-root" (include "rstuf-webapp.fullname" .) }}
{{- end }}
{{- end }}
