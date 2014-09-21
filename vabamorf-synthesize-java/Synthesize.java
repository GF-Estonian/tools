import ee.filosoft.vabamorf.Linguistic;
import ee.filosoft.vabamorf.Linguistic.MorphInfo;
import java.io.*;

class Synthesize {

    private static String[] forms_S = {"sg n", "sg g", "sg p", "sg ill", "pl g", "pl p"};
    private static String[] forms_V = {"ma", "da", "b", "takse", "ge", "s", "nud", "tud"};

    public static void main(String[] args) throws IOException {

        Linguistic linguistic = new Linguistic();
        linguistic.guess = true;
        //linguistic.phon = true; // TODO: future work

        boolean success = linguistic.open("et.dct");

        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));

        MorphInfo mi = new MorphInfo();
        //mi.root = defined dynamically
        mi.ending = "";
        mi.clitic = "";
        mi.pos = args[0].charAt(0);
        //mi.form = defined dynamically

        String[] forms = forms_S;
        if (mi.pos == 'V') {
            forms = forms_V;
        }

        while ((mi.root = in.readLine()) != null) {
            int form_count = 0;
            for (String form : forms) {
                mi.form = form;
                MorphInfo[] synths = makeForms(linguistic, mi);

                if (synths == null || synths.length == 0) {
                    System.err.println("Warning: no forms: " + mi.root + "_" + mi.pos + "_" + mi.form);
                } else {
                    for (int k = 0; k < synths.length; k++) {
                        // We accept only forms that have the form-field set to the original form identifier.
                        // This is needed to get a more meaningful output for some adjectives.
                        // As an exception we also cover "sg ill"/"adt".
                        if (form.equals(synths[k].form) || form.equals("sg ill") && "adt".equals(synths[k].form)) {
                            System.out.print(synths[k].root + synths[k].ending);
                            if (k < synths.length - 1) {
                                System.out.print('|');
                            }
                        }
                    }
                }
                if (++form_count < forms.length) {
                    System.out.print(", ");
                }
            }
            System.out.println();
        }

        linguistic.close();
    }

    private static MorphInfo[] makeForms(Linguistic linguistic, MorphInfo mi) {
        if (mi.form.equals("sg ill")) {
            MorphInfo[] A = linguistic.synthesize(mi, "");
            mi.form = "adt";
            MorphInfo[] B = linguistic.synthesize(mi, "");
            int aLen = A.length;
            int bLen = B.length;
            MorphInfo[] C = new MorphInfo[aLen+bLen];
            System.arraycopy(A, 0, C, 0, aLen);
            System.arraycopy(B, 0, C, aLen, bLen);
            return C;
        }
        return linguistic.synthesize(mi, "");
    }

}
