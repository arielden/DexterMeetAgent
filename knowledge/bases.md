# Estadística y Exploración de Datos - Base de Conocimiento para ChromaDB

## CONCEPTOS FUNDAMENTALES DE ESTADÍSTICA

### Definiciones Básicas
- **Estadística**: conjunto de métodos para manejar obtención, presentación y análisis de observaciones numéricas
- **Población**: conjunto completo de individuos u objetos de estudio
- **Muestra**: subconjunto representativo de la población
- **Parámetro**: medida numérica que describe característica de la población
- **Estadístico**: medida numérica que describe característica de la muestra
- **Variable**: característica que se estudia en cada individuo

### Clasificación de Variables
- **Variables cualitativas**: se responden con palabras (nominales u ordinales)
- **Variables cuantitativas**: se responden con números (discretas o continuas)

### Escalas de Medida
- **Nominal**: categorías sin orden (ej: color de ojos)
- **Ordinal**: categorías con orden jerárquico (ej: nivel educativo)
- **Intervalos**: valores numéricos con distancias significativas
- **Razón**: valores numéricos con cero absoluto y proporciones

## ESTADÍSTICA DESCRIPTIVA

### Organización de Datos
- **Distribución de frecuencias**: organización en intervalos de clase
- **Regla de Sturges**: \( k = 1 + 3.3 \log(n) \) para número de clases
- **Componentes**: frecuencia absoluta, acumulada, relativa, relativa acumulada

### Medidas de Tendencia Central
- **Media aritmética**: \(\overline{X} = \frac{\sum x_i}{n}\)
- **Mediana**: valor central de datos ordenados
- **Moda**: valor que más se repite

### Medidas de Dispersión
- **Rango**: diferencia entre máximo y mínimo
- **Varianza**: \( s^2 = \frac{\sum (x_i - \overline{x})^2}{n} \)
- **Desviación estándar**: \( s = \sqrt{s^2} \)
- **Coeficiente de variación**: \( CV = \frac{s}{\overline{x}} \times 100\% \)

### Medidas de Forma
- **Asimetría**: 
  - Coeficiente de Pearson: \( ASP = \frac{3(\overline{X} - Md)}{s} \)
  - Coeficiente de Fisher: \( ASF = \frac{\sum (x_i - \overline{x})^3}{ns^3} \)
- **Kurtosis**: medida de concentración alrededor de la media

## PROBABILIDAD

### Conceptos Básicos
- **Experimento aleatorio**: resultado conocido pero no predecible
- **Espacio muestral (S)**: conjunto de todos resultados posibles
- **Suceso**: subconjunto del espacio muestral
- **Probabilidad clásica**: \( P(A) = \frac{\text{casos favorables}}{\text{casos posibles}} \)
- **Probabilidad frecuencial**: basada en frecuencia relativa

### Teoremas de Probabilidad
- **Probabilidad complementaria**: \( P(\bar{A}) = 1 - P(A) \)
- **Regla de la adición**: \( P(A \cup B) = P(A) + P(B) - P(A \cap B) \)
- **Probabilidad condicional**: \( P(A/B) = \frac{P(A \cap B)}{P(B)} \)
- **Regla multiplicativa**: \( P(A \cap B) = P(B) \cdot P(A/B) \)

### Independencia de Sucesos
- Dos sucesos son independientes si: \( P(A/B) = P(A) \) o \( P(B/A) = P(B) \)

### Teoremas Avanzados
- **Ley de probabilidad total**: \( P(B) = \sum P(B/A_i) \cdot P(A_i) \)
- **Teorema de Bayes**: \( P[A_n / B] = \frac{P[B / A_n] \cdot P[A_n]}{\sum P[B / A_i] \cdot P[A_i]} \)

## VARIABLES ALEATORIAS Y DISTRIBUCIONES

### Variables Aleatorias
- **Variable aleatoria discreta**: toma valores contables
- **Variable aleatoria continua**: toma valores en intervalo continuo
- **Función de probabilidad**: \( p(x_i) = P(X = x_i) \)
- **Función de distribución**: \( F(x_i) = P(X \leq x_i) \)

### Medidas de Resumen
- **Valor esperado**: \( E(X) = \sum X \cdot p(X) \)
- **Varianza**: \( \sigma^2(X) = \sum X^2 \cdot p(X) - [E(X)]^2 \)

### Distribución Binomial
- **Propiedades**:
  - n repeticiones independientes
  - Dos resultados: éxito (p) o fracaso (q=1-p)
  - Probabilidad constante
- **Función de probabilidad**: \( P(X = x) = \binom{n}{x} p^x q^{n-x} \)
- **Media y varianza**: \( E(X) = np \), \( \sigma^2(X) = npq \)

### Distribución Normal
- **Características**:
  - Forma de campana y simétrica
  - Media, mediana y moda coinciden
  - Completamente determinada por μ y σ
- **Función de densidad**: \( f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}} \)
- **Estandarización**: \( z = \frac{x - \mu}{\sigma} \)
- **Regla empírica**:
  - μ ± σ: 68% de probabilidad
  - μ ± 2σ: 95% de probabilidad
  - μ ± 3σ: 99% de probabilidad

## DISTRIBUCIONES MUESTRALES

### Teoría del Muestreo
- **Muestra aleatoria**: seleccionada mediante procedimiento aleatorio
- **Muestra representativa**: refleja características de la población
- **Error muestral**: variación natural entre muestras
- **Sesgo muestral**: error sistemático en método de muestreo

### Distribución Muestral de Medias
- **Teorema Central del Límite**: para n > 30 o población normal, la distribución muestral de medias es aproximadamente normal
- **Media**: \( \mu_{\overline{X}} = \mu \)
- **Desviación estándar**: \( \sigma_{\overline{X}} = \frac{\sigma}{\sqrt{n}} \)
- **Factor corrección población finita**: \( \sqrt{\frac{N - n}{N - 1}} \)

### Distribución Muestral de Proporciones
- **Media**: \( \mu_p = P \)
- **Desviación estándar**: \( \sigma_p = \sqrt{\frac{P(1-P)}{n}} \)
- **Condición normalidad**: \( np \geq 5 \) y \( n(1-p) \geq 5 \)

## ESTIMACIÓN DE PARÁMETROS

### Estimación Puntual
- **Estimador**: función de la muestra que aproxima parámetro
- **Propiedades buenos estimadores**: insesgado, consistente, eficiente
- **Estimadores comunes**:
  - Media muestral para μ
  - Varianza muestral para σ²
  - Proporción muestral para P

### Estimación por Intervalos
- **Intervalo de confianza**: rango que contiene parámetro con cierta confianza
- **Nivel de confianza**: probabilidad de que intervalo contenga parámetro

### Intervalos de Confianza para Media
- **σ conocida**: \( \overline{X} \pm Z_{1-\alpha/2} \cdot \frac{\sigma}{\sqrt{n}} \)
- **σ desconocida, n > 30**: \( \overline{X} \pm Z_{1-\alpha/2} \cdot \frac{S}{\sqrt{n}} \)
- **σ desconocida, n < 30**: \( \overline{X} \pm t_{n-1,1-\alpha/2} \cdot \frac{S}{\sqrt{n}} \)

### Intervalo de Confianza para Proporción
- **Fórmula**: \( p \pm Z_{1-\alpha/2} \cdot \sqrt{\frac{p(1-p)}{n}} \)
- **Condiciones**: muestra grande, np ≥ 5, n(1-p) ≥ 5

### Tamaño de Muestra
- **Para media**: \( n = \left( \frac{Z_{1-\alpha/2} \cdot \sigma}{d} \right)^2 \)
- **Para proporción**: \( n = \left( \frac{Z_{1-\alpha/2}}{d} \right)^2 \cdot p(1-p) \)
- **Factores que influyen**: variabilidad, precisión, confiabilidad

## PRUEBAS DE HIPÓTESIS

### Conceptos Fundamentales
- **Hipótesis nula (H₀)**: hipótesis de no efecto o no diferencia
- **Hipótesis alternativa (H₁)**: hipótesis de investigación
- **Nivel de significación (α)**: probabilidad error tipo I
- **Valor p**: probabilidad de obtener resultados tan extremos asumiendo H₀ cierta
- **Región crítica**: valores que llevan a rechazar H₀

### Tipos de Pruebas
- **Bilateral**: H₁: parámetro ≠ valor
- **Unilateral derecha**: H₁: parámetro > valor
- **Unilateral izquierda**: H₁: parámetro < valor

### Errores en Pruebas de Hipótesis
- **Error Tipo I**: rechazar H₀ cuando es verdadera (probabilidad α)
- **Error Tipo II**: no rechazar H₀ cuando es falsa (probabilidad β)
- **Potencia de la prueba**: 1 - β

### Procedimiento General
1. Plantear H₀ y H₁
2. Especificar nivel de significación α
3. Seleccionar estadístico de prueba
4. Establecer regla de decisión
5. Calcular estadístico y valor p
6. Tomar decisión e interpretar

### Pruebas para Medias
- **Una muestra**: comparar media muestral con valor hipotético
- **Dos muestras independientes**: comparar medias de grupos diferentes
- **Dos muestras relacionadas**: comparar mediciones pareadas

### Pruebas para Proporciones
- **Una muestra**: comparar proporción muestral con valor hipotético
- **Dos muestras**: comparar proporciones de dos grupos

## COMPARACIÓN DE PROMEDIOS POBLACIONALES

### Muestras Independientes
- **Características**: grupos diferentes, observaciones no relacionadas
- **Prueba homogeneidad varianzas**: preliminar para determinar igualdad de varianzas
- **Estadístico de prueba**: depende de igualdad o desigualdad de varianzas

### Muestras Relacionadas
- **Características**: mismas unidades en diferentes condiciones
- **Variable diferencia**: d = X₁ - X₂
- **Hipótesis equivalentes**: H₀: μ₁ = μ₂ ⇔ H₀: μ_d = 0

### Aplicaciones Prácticas
- Estudios antes-después
- Comparación de tratamientos
- Pruebas de efectividad
- Estudios de equivalencia

## TÉCNICAS DE MUESTREO

### Muestreo Aleatorio Simple
- Cada elemento tiene igual probabilidad de ser seleccionado
- Requiere marco muestral completo

### Muestreo Estratificado
- Población dividida en estratos homogéneos
- Muestreo aleatorio dentro de cada estrato

### Muestreo por Conglomerados
- Población dividida en grupos naturales
- Muestreo de conglomerados completos

### Muestreo Sistemático
- Selección cada k-ésimo elemento después de inicio aleatorio

## CONCEPTOS CLAVE PARA ANÁLISIS ESTADÍSTICO

### Valores Críticos Comunes
- **Nivel 95%**: Z = 1.96, t ≈ 2.0 (grados libertad altos)
- **Nivel 99%**: Z = 2.58, t ≈ 2.6 (grados libertad altos)

### Condiciones para Inferencia Válida
- **Normalidad**: población normal o muestra grande (n ≥ 30)
- **Independencia**: observaciones independientes
- **Aleatoriedad**: muestra seleccionada aleatoriamente

### Interpretación de Resultados
- **Significación estadística**: valor p < α
- **Significación práctica**: magnitud del efecto
- **Precisión estimación**: amplitud del intervalo de confianza
- **Generalización**: aplicabilidad a población de interés