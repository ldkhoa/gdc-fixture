package com.gooddata.fixture;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.Optional;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Collectors;

import org.apache.maven.model.Dependency;
import org.apache.maven.model.Model;
import org.apache.maven.model.io.xpp3.MavenXpp3Reader;
import org.codehaus.plexus.util.xml.pull.XmlPullParserException;

public class ResourceManagement {

    private JarFile artifact;

    public ResourceManagement() {
        this.artifact = getArtifact();
    }

    /**
     * Read content from resource file in Fixture Jar artifact
     * @param resourceDir path to resource file in Fixture Jar artifact. e.g: GoodFix/1/README.md
     * @return Content of resource file
     * @throws IOException if an I/O error has occurred
     */
    public String getResourceAsString(String resourceDir) throws IOException {
        InputStream is = artifact.getInputStream(artifact.getEntry(resourceDir));
        return new BufferedReader(new InputStreamReader(is)).lines().collect(Collectors.joining("\n"));
    }

    /**
     * Extract resources from given template in Fixture Jar artifact and copy to new directory
     * @param template the resource template. e.g: GOODFIX, GOODSALES,...
     * @param desDir the destination directory
     * @throws IOException if an I/O error has occurred
     */
    public void copyResources(ResourceTemplate template, String desDir) throws IOException {
        copyResources(template.getPath(), desDir);
    }

    /**
     * Extract resources (can be folder or file) in Fixture Jar artifact and copy to new directory 
     * @param resourcesDir resources directory in Fixture Jar artifact. e.g: GoodFix/1/, GoodFix/1/README.md
     * @param desDir the destination directory
     * @throws IOException if an I/O error has occurred
     */
    public void copyResources(String resourcesDir, String desDir) throws IOException {
        Enumeration<JarEntry> entries = artifact.entries();
        while (entries.hasMoreElements()) {
            JarEntry entry = entries.nextElement();
            if (entry.getName().startsWith(resourcesDir)) {
                if (!entry.isDirectory()) {
                    extractResourceToFile(entry, desDir);
                }
            }
        }
    }

    private void extractResourceToFile(JarEntry resource, String desDir) throws IOException {
        File file = new File(desDir, resource.getName());
        if (!file.getParentFile().exists()) {
            file.getParentFile().mkdirs();
        }

        try (InputStream is = artifact.getInputStream(resource);
                FileOutputStream os = new FileOutputStream(file)) {
            while (is.available() > 0) {
                os.write(is.read());
            }
        }
    }

    private String getArtifactVersion() {
        try {
            MavenXpp3Reader reader = new MavenXpp3Reader();
            Model model = reader.read(new FileReader("pom.xml"));
            Optional<Dependency> dependency;

            while (!(dependency = model.getDependencies()
                        .stream()
                        .filter(d -> "gdc-fixture".equals(d.getArtifactId()))
                        .findFirst())
                    .isPresent()) {
                model = reader.read(new FileReader("../pom.xml"));
            }
            return dependency.get().getVersion();

        } catch (IOException e) {
            throw new RuntimeException("Missing pom.xml!");
        } catch (XmlPullParserException e) {
            throw new RuntimeException("There has an error when parsing pom.xml!");
        }
    }

    private JarFile getArtifact() {
        String artifactName = "gdc-fixture-" + getArtifactVersion() + ".jar";

        try {
            File artifact = Files.walk(Paths.get(System.getProperty("user.home") + "/.m2/repository"))
                    .map(p -> p.toFile())
                    .filter(f -> f.getName().equals(artifactName))
                    .findFirst()
                    .get();
            return new JarFile(artifact);

        } catch (IOException e) {
            throw new RuntimeException(artifactName + " not found!");
        }
    }

    public enum ResourceTemplate {
        GOODFIX("GoodFix"),
        GOODSALES("GoodSales"),
        SINGLE_INVOICE("SingleInvoice");

        private String path;

        private ResourceTemplate(String path) {
            this.path = path;
        }

        public String getPath() {
            return path;
        }
    }
}
