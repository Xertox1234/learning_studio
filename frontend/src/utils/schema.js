/**
 * Schema.org structured data utilities for SEO
 */

/**
 * Generate Course Schema.org structured data
 */
export const generateCourseSchema = (course) => {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Course',
    name: course.title,
    description: course.short_description,
    courseCode: course.course_code,
    
    // Provider information
    provider: {
      '@type': 'Organization',
      name: 'Python Learning Studio',
      url: window.location.origin
    },
    
    // Course details
    educationalLevel: course.difficulty_level,
    teaches: course.learning_objectives?.map(obj => obj.title) || [],
    
    // Pricing
    ...(course.is_free ? {
      isAccessibleForFree: true
    } : {
      offers: {
        '@type': 'Offer',
        price: course.price,
        priceCurrency: 'USD',
        category: 'Educational'
      }
    }),
    
    // Instructor
    ...(course.instructor && {
      instructor: {
        '@type': 'Person',
        name: course.instructor.name,
        email: course.instructor.email
      }
    }),
    
    // Course requirements
    ...(course.prerequisites && {
      coursePrerequisites: course.prerequisites.replace(/<[^>]*>/g, '') // Strip HTML
    }),
    
    // Estimated duration
    ...(course.estimated_duration && {
      timeRequired: course.estimated_duration
    }),
    
    // Course image
    ...(course.course_image && {
      image: course.course_image
    }),
    
    // Course syllabus/curriculum
    ...(course.lessons?.length > 0 && {
      syllabusSections: course.lessons.map((lesson, index) => ({
        '@type': 'Syllabus',
        position: lesson.lesson_number || index + 1,
        name: lesson.title,
        description: lesson.intro,
        timeRequired: lesson.estimated_duration
      }))
    }),
    
    // Categories as course subjects
    ...(course.categories?.length > 0 && {
      about: course.categories.map(cat => ({
        '@type': 'Thing',
        name: cat.name
      }))
    }),
    
    // Keywords from tags
    ...(course.tags?.length > 0 && {
      keywords: course.tags.join(', ')
    }),
    
    // URL
    url: window.location.href,
    
    // Publisher
    publisher: {
      '@type': 'Organization',
      name: 'Python Learning Studio',
      url: window.location.origin
    }
  }
  
  return schema
}

/**
 * Generate Lesson Schema.org structured data
 */
export const generateLessonSchema = (lesson, course) => {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'LearningResource',
    name: lesson.title,
    description: lesson.intro,
    
    // Educational properties
    educationalLevel: course?.difficulty_level || 'beginner',
    learningResourceType: 'lesson',
    teaches: lesson.objectives || [],
    
    // Part of course
    ...(course && {
      isPartOf: {
        '@type': 'Course',
        name: course.title,
        url: `${window.location.origin}/learning/courses/${course.slug}`
      }
    }),
    
    // Time required
    ...(lesson.estimated_duration && {
      timeRequired: lesson.estimated_duration
    }),
    
    // Position in course
    ...(lesson.lesson_number && {
      position: lesson.lesson_number
    }),
    
    // Prerequisites
    ...(lesson.prerequisites && {
      educationalUse: lesson.prerequisites.replace(/<[^>]*>/g, '') // Strip HTML
    }),
    
    // URL
    url: window.location.href,
    
    // Publisher
    publisher: {
      '@type': 'Organization',
      name: 'Python Learning Studio',
      url: window.location.origin
    }
  }
  
  return schema
}

/**
 * Generate Exercise Schema.org structured data
 */
export const generateExerciseSchema = (exercise, lesson, course) => {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'LearningResource',
    name: exercise.title,
    description: exercise.description?.replace(/<[^>]*>/g, '') || '', // Strip HTML
    
    // Educational properties
    educationalLevel: course?.difficulty_level || exercise.difficulty || 'beginner',
    learningResourceType: 'exercise',
    
    // Exercise specific properties
    interactivityType: 'active',
    educationalUse: 'practice',
    
    // Programming language
    ...(exercise.programming_language && {
      programmingLanguage: exercise.programming_language
    }),
    
    // Difficulty
    ...(exercise.difficulty && {
      typicalAgeRange: exercise.difficulty === 'easy' ? '13-18' : 
                      exercise.difficulty === 'medium' ? '16-25' : '18+'
    }),
    
    // Part of lesson and course
    ...(lesson && {
      isPartOf: {
        '@type': 'LearningResource',
        name: lesson.title,
        url: `${window.location.origin}/learning/courses/${course?.slug}/lessons/${lesson.slug}`
      }
    }),
    
    // Time constraints
    ...(exercise.time_limit && {
      timeRequired: `PT${exercise.time_limit}M` // ISO 8601 duration format
    }),
    
    // Points/scoring
    ...(exercise.points && {
      educationalCredentialAwarded: `${exercise.points} points`
    }),
    
    // URL
    url: window.location.href,
    
    // Publisher
    publisher: {
      '@type': 'Organization',
      name: 'Python Learning Studio',
      url: window.location.origin
    }
  }
  
  return schema
}

/**
 * Generate Organization Schema.org structured data
 */
export const generateOrganizationSchema = () => {
  return {
    '@context': 'https://schema.org',
    '@type': 'EducationalOrganization',
    name: 'Python Learning Studio',
    description: 'AI-powered Python programming education platform with interactive courses, real-time code execution, and community support.',
    url: window.location.origin,
    
    // Contact information
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer service',
      email: 'support@pythonlearning.studio'
    },
    
    // Educational focus
    educationalCredentialAwarded: 'Programming Certificate',
    hasCredential: {
      '@type': 'EducationalOccupationalCredential',
      credentialCategory: 'certificate',
      educationalLevel: 'Beginner to Advanced'
    },
    
    // Services offered
    makesOffer: {
      '@type': 'Offer',
      itemOffered: {
        '@type': 'Course',
        name: 'Python Programming Courses',
        description: 'Comprehensive Python programming education with AI assistance'
      }
    }
  }
}

/**
 * Inject structured data into page head
 */
export const injectStructuredData = (schema) => {
  // Remove existing structured data for this page
  const existingScripts = document.querySelectorAll('script[type="application/ld+json"][data-schema]')
  existingScripts.forEach(script => script.remove())
  
  // Create new structured data script
  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.setAttribute('data-schema', 'true')
  script.textContent = JSON.stringify(schema, null, 2)
  
  // Add to document head
  document.head.appendChild(script)
}

/**
 * React hook for managing structured data
 */
export const useStructuredData = (schema) => {
  React.useEffect(() => {
    if (schema) {
      injectStructuredData(schema)
    }
    
    // Cleanup on unmount
    return () => {
      const scripts = document.querySelectorAll('script[type="application/ld+json"][data-schema]')
      scripts.forEach(script => script.remove())
    }
  }, [schema])
}